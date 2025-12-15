from sqlalchemy.orm import Session
from sqlalchemy import desc
from api.models import UserHistory, QuizScore, StudentSkillIndex, LearningPath, TelemetryLog
from api.ml.engine import predict_dependency_probability
from api.services.telemetry_service import aggregate_session_features

WEIGHT_RETENTION = 0.4
WEIGHT_INDEPENDENCE = 0.3
WEIGHT_QUALITY = 0.3

def calculate_ssi(user_id: int, db: Session) -> float:
    recent_quizzes = db.query(QuizScore)\
        .filter(QuizScore.user_id == user_id)\
        .order_by(desc(QuizScore.created_at))\
        .limit(5)\
        .all()
    
    if not recent_quizzes:
        R = 50.0
    else:
        scores = [(q.score / q.total_questions) * 100 for q in recent_quizzes if q.total_questions > 0]
        R = sum(scores) / len(scores) if scores else 0.0
        R = sum(scores) / len(scores) if scores else 0.0

    latest_log = db.query(TelemetryLog).filter(TelemetryLog.user_id == user_id).order_by(desc(TelemetryLog.created_at)).first()
    session_id = latest_log.session_id if latest_log else "unknown_session"

    features = aggregate_session_features(user_id, session_id, db)
    dependency_prob = predict_dependency_probability(features)
    I = (1.0 - dependency_prob) * 100.0

    last_chats = db.query(UserHistory)\
        .filter(UserHistory.user_id == user_id)\
        .order_by(desc(UserHistory.id))\
        .limit(10)\
        .all()
    
    if not last_chats:
        Q = 50.0
    else:
        avg_len = sum([len(c.prompt) for c in last_chats]) / len(last_chats)
        Q = max(0.0, min(100.0, (avg_len / 200) * 100))

    ssi_value = (WEIGHT_RETENTION * R) + (WEIGHT_INDEPENDENCE * I) + (WEIGHT_QUALITY * Q)
    return round(ssi_value, 2)

def update_student_profile(user_id: int, db: Session):
    new_ssi = calculate_ssi(user_id, db)
    
    if new_ssi < 40.0:
        bucket = "Weak"
        path_type = "Reinforcement"
def update_student_profile(user_id: int, new_ssi: float, dependency_prob: float, db: Session):
    
    current_skill = db.query(StudentSkillIndex).filter(StudentSkillIndex.user_id == user_id).first()
    current_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()

    old_ssi = current_skill.index_value if current_skill else 50.0
    current_bucket = current_skill.bucket if current_skill else "Moderate"
    
    if not current_skill:
        current_skill = StudentSkillIndex(user_id=user_id, index_value=new_ssi, bucket="Moderate")
        db.add(current_skill)
    else:
        current_skill.index_value = new_ssi
        
    bucket = "Weak" if new_ssi < 40 else ("Strong" if new_ssi > 75 else "Moderate")
    current_skill.bucket = bucket
    
    dependency_level = "High" if dependency_prob > 0.6 else "Low"
    
    reward = 0
    if new_ssi > old_ssi:
        reward += 10
    elif new_ssi < old_ssi:
        reward -= 10
    
    if dependency_prob < 0.4:
        reward += 5
        
    last_action = current_path.path_type if current_path else "Balanced"
    
    rl_agent.learn(current_bucket, dependency_level, last_action, reward, bucket, dependency_level)
    

    next_action_path = rl_agent.choose_action(bucket, dependency_level)
    
    if not current_path:
        current_path = LearningPath(
             user_id=user_id, 
             path_type=next_action_path, 
             current_difficulty=1
        )
        db.add(current_path)
    else:
        current_path.path_type = next_action_path
        
    if bucket == "Weak":
        current_path.current_difficulty = 1
    elif bucket == "Strong":
        current_path.current_difficulty = 3
    else:
        current_path.current_difficulty = 2

    path_record = current_path 
    path_record.path_type = next_action_path
    
    db.commit()

    return {
        "ssi": new_ssi,
        "bucket": bucket,
        "dependency_prob": dependency_prob,
        "learning_path": next_action_path,
        "rl_reward": reward
    }