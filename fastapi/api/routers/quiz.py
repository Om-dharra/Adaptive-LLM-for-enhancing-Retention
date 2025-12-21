from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import os
from groq import Groq # Import Groq
from api.services.adaptive_engine import update_student_profile
from api.deps import get_db
from api.models import UserHistory, QuizScore
from api.schemas import GeneratedQuiz, QuizScoreCreate, QuizScoreResponse, QuizGenerateRequest
from api.deps import get_current_user

# Initialize Groq Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


@router.post("/generate", response_model=GeneratedQuiz)
async def generate_quiz_from_context(
    request: Optional[QuizGenerateRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user['user_id']
    
    query = db.query(UserHistory).filter(UserHistory.user_id == user_id)
    
    if request and request.session_id:
        query = query.filter(UserHistory.session_id == request.session_id)
        
    recent_history = query.order_by(desc(UserHistory.id))\
        .limit(3)\
        .all()
    
    if not recent_history:
        raise HTTPException(status_code=400, detail="Not enough chat history to generate a quiz.")
    

    context_text = "\n".join([f"Student: {h.prompt}\nAI Tutor: {h.response}" for h in reversed(recent_history)])

    # Identify Weak Topics (< 70% score)
    weak_scores = db.query(QuizScore).filter(
        QuizScore.user_id == user_id,
        (QuizScore.score / QuizScore.total_questions) < 0.7
    ).all()
    
    weak_topics = list(set([ws.topic_tag for ws in weak_scores if ws.topic_tag]))
    weak_topics_str = ", ".join(weak_topics) if weak_topics else "None"

    prompt = f"""
    Based strictly on the following conversation context, generate a Micro-Quiz to test the student's retention.
    
    PRIORITY FOCUS: The student has previously struggled with: {weak_topics_str}.
    If relevant to the context below, prioritize questions on these topics to reinforce learning.
    
    CONTEXT:
    {context_text}
    
    INSTRUCTIONS:
    1. Create 5 Multiple Choice Questions (MCQs).
    2. Include 1 distractor answer that addresses a common misconception.
    3. Output must be valid JSON matching this structure:
    {{
        "topic": "Short Topic Name",
        "questions": [
            {{
                "id": 1,
                "question_text": "...",
                "options": [
                    {{"id": "A", "text": "..."}},
                    {{"id": "B", "text": "..."}},
                    {{"id": "C", "text": "..."}},
                    {{"id": "D", "text": "..."}}
                ],
                "correct_option_id": "A",
                "explanation": "Why A is correct..."
            }}
        ]
    }}
    """

    try:
        # Generate Quiz using Groq (Llama 3)
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            response_format={"type": "json_object"} # Force JSON mode
        )

        response_text = chat_completion.choices[0].message.content
        quiz_data = json.loads(response_text)
        
        return quiz_data

    except Exception as e:
        print(f"Quiz Gen Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.post("/submit", response_model=QuizScoreResponse)
async def submit_quiz_score(
    score_data: QuizScoreCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    new_score = QuizScore(
        user_id=current_user['user_id'],
        topic_tag=score_data.topic_tag,
        score=score_data.score,
        total_questions=score_data.total_questions,
        attempts=score_data.attempts
    )
    
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    update_student_profile(user_id=current_user['user_id'], db=db)


    return new_score