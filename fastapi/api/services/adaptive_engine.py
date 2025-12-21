from sqlalchemy.orm import Session
from sqlalchemy import desc
from api.models import UserHistory, QuizScore, StudentSkillIndex, LearningPath, TelemetryLog
from api.ml.engine import predict_dependency_probability
from api.services.telemetry_service import aggregate_session_features

import torch
from api.services.dkt_model import DKTModel

NUM_SKILLS = 50
model = DKTModel(num_skills=NUM_SKILLS)

WEIGHT_RETENTION = 0.4
WEIGHT_INDEPENDENCE = 0.3
WEIGHT_QUALITY = 0.3

def get_student_mastery(interaction_history):

    if not interaction_history:
        return [0.5] * NUM_SKILLS 
        
    input_seq = []
    for item in interaction_history:
        skill = item['skill_id']
        correct = item['correct']
        
        input_id = skill + (NUM_SKILLS * correct)
        input_seq.append(input_id)
        
    input_tensor = torch.tensor([input_seq])
    
    with torch.no_grad():
        predictions, _ = model(input_tensor)
    
    final_state_predictions = predictions[0, -1, :]
    return final_state_predictions.tolist()

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
    return {
        "ssi": round(ssi_value, 2),
        "dependency_prob": dependency_prob
    }

def update_student_profile(user_id: int, db: Session, current_session_id: str = None):
    
    # Calculate SSI using real data (Quiz Scores + Telemetry + Chat History)
    metrics = calculate_ssi(user_id, db)
    ssi = metrics['ssi']
    dependency_prob = metrics['dependency_prob']
    
    # Update Skill Index Record
    skill_record = db.query(StudentSkillIndex).filter_by(user_id=user_id).first()
    if not skill_record:
        skill_record = StudentSkillIndex(user_id=user_id)
        db.add(skill_record)
    
    skill_record.index_value = ssi
    
    # Determine Strength Bucket
    if ssi < 40:
        skill_record.bucket = "Weak"
    elif ssi > 70:
        skill_record.bucket = "Strong"
    else:
        skill_record.bucket = "Moderate"

    # Update Learning Path
    path_record = db.query(LearningPath).filter_by(user_id=user_id).first()
    if not path_record:
        path_record = LearningPath(user_id=user_id)
        db.add(path_record)

    if ssi < 40:
        path_record.path_type = "Reinforcement" 
    elif ssi > 70:
        path_record.path_type = "Acceleration"
    else:
        path_record.path_type = "Balanced"

    db.commit()
    print(f"DEBUG: XGBoost Prob: {dependency_prob:.2f} | New SSI: {ssi:.2f} | Path: {path_record.path_type} | Bucket: {skill_record.bucket}")