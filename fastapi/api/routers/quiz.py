from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import google.generativeai as genai
import json
import os
from api.services.adaptive_engine import update_student_profile
from api.deps import get_db
from api.models import UserHistory, QuizScore
from api.schemas import GeneratedQuiz, QuizScoreCreate, QuizScoreResponse
from api.deps import get_current_user

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


@router.post("/generate", response_model=GeneratedQuiz)
async def generate_quiz_from_context(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user['user_id']
    
    recent_history = db.query(UserHistory)\
        .filter(UserHistory.user_id == user_id)\
        .order_by(desc(UserHistory.id))\
        .limit(3)\
        .all()
    
    if not recent_history:
        raise HTTPException(status_code=400, detail="Not enough chat history to generate a quiz.")
    

    context_text = "\n".join([f"Student: {h.prompt}\nAI Tutor: {h.response}" for h in reversed(recent_history)])
  
    prompt = f"""
    Based strictly on the following conversation context, generate a Micro-Quiz to test the student's retention.
    
    CONTEXT:
    {context_text}
    
    INSTRUCTIONS:
    1. Create 3 Multiple Choice Questions (MCQs).
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

        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(prompt)
        quiz_data = json.loads(response.text)
        
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