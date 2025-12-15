from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import func
from typing import List
import os
import numpy as np
import google.generativeai as genai
from api.deps import get_db
from api.models import User, UserHistory, LearningPath
from api.schemas import UserHistoryCreate, UserHistoryResponse
from api.deps import get_current_user
from typing import List
from api.services.adaptive_engine import update_student_profile


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

def calculate_cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    
    a = np.array(vec_a)
    b = np.array(vec_b)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)

def get_embedding(text: str):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []

def get_system_persona(learning_path: LearningPath, struggle_override: bool = False) -> str:

    if struggle_override:
        return (
            "SYSTEM ALERT: The user is repeating a question, indicating a retention failure. "
            "Do NOT answer the question directly. "
            "Instead, ask a simple guiding question (Socratic Method) to help them realize the answer. "
            "Be patient and encouraging."
        )

    # Standard Persona Logic
    if not learning_path:
        return "You are a helpful and clear computer science tutor."

    mode = learning_path.path_type 
    
    if mode == "Reinforcement":
        return "You are a supportive tutor. Use analogies and hints. Do not give full code answers."
    elif mode == "Acceleration":
        return "You are a strict technical examiner. Be concise and challenge the student."
    else:
        return "You are a balanced tutor. Explain clearly."

def call_llm_service(system_prompt: str, chat_history: List[dict], user_message: str) -> str:

    try:
       
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_prompt
        )

        gemini_history = []
        for msg in chat_history:
            gemini_history.append({"role": "user", "parts": [msg['prompt']]})
            gemini_history.append({"role": "model", "parts": [msg['response']]})

        chat = model.start_chat(history=gemini_history)

    
        response = chat.send_message(user_message)
        
        return response.text

    except Exception as e:
        print(f"Gemini API Error: {e}")
    
        return "I'm having trouble connecting to my brain right now. Please try again."

@router.post("/message", response_model=UserHistoryResponse)
async def chat_with_ai(
    chat_request: UserHistoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['user_id']
        prompt = chat_request.prompt
        session_id = chat_request.session_id

        # 1. Handle Session Creation
        import uuid
        if not session_id:
            session_id = str(uuid.uuid4())
            # Generate a title for the new session based on the first prompt
            try:
                model = genai.GenerativeModel("gemini-flash-latest")
                title_response = model.generate_content(f"Generate a short 3-5 word title for a chat that starts with: '{prompt}'")
                title = title_response.text.strip().replace('"', '')
            except:
                title = "New Chat"
        else:
            title = None # Title already exists for this session

        # 2. Get User Context (Learning Path & Skill Index)
        learning_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()
        
        # 3. Retrieve recent history for THIS SESSION for context
        history_limit = 5
        recent_history = db.query(UserHistory)\
            .filter(UserHistory.user_id == user_id, UserHistory.session_id == session_id)\
            .order_by(desc(UserHistory.created_at))\
            .limit(history_limit)\
            .all()
        
        chat_history_list = [{"prompt": h.prompt, "response": h.response} for h in reversed(recent_history)]

        # 4. Check for Struggle / Retention Failure (Vector Similarity)
        current_embedding = get_embedding(prompt)
        struggle_detected = False
        
        if recent_history and current_embedding:
            last_msg = recent_history[0]
            if last_msg.embedding_vector:
                similarity = calculate_cosine_similarity(current_embedding, last_msg.embedding_vector)
                if similarity > 0.85: # High similarity = User repeating themselves
                    struggle_detected = True

        # 5. Determine Persona & Call LLM
        system_persona = get_system_persona(learning_path, struggle_override=struggle_detected)
        ai_response = call_llm_service(system_persona, chat_history_list, prompt)

        # 6. Adaptive Engine Update (Simulated for every interaction for now)
        # In a real app, we might only update after a "session" or significant event
        # Here we do a dry run or small update if needed. 
        # For now, we rely on QUIZ updates to drive the engine, but we could add "Heuristic" updates here.
        
        # 7. Save Interaction
        new_interaction = UserHistory(
            user_id=user_id,
            session_id=session_id,
            title=title if title else None, # Only save title on first message of session
            prompt=prompt,
            response=ai_response,
            embedding_vector=current_embedding if current_embedding else []
        )
        
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)
        
        return new_interaction

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[UserHistoryResponse])
async def get_all_history(
    skip: int = 0,
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    history = db.query(UserHistory)\
        .filter(UserHistory.user_id == current_user['user_id'])\
        .order_by(desc(UserHistory.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return history

@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    history_item = db.query(UserHistory).filter(
        UserHistory.id == history_id,
        UserHistory.user_id == current_user['user_id'] # Security check: Must belong to user
    ).first()

    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found")

    db.delete(history_item)
    db.commit()
    
    return None

@router.get("/sessions")
async def get_sessions(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user['user_id']
    # Group by session_id to get unique sessions and their titles
    sessions = db.query(
        UserHistory.session_id, 
        UserHistory.title, 
        func.max(UserHistory.created_at).label('last_updated')
    )\
    .filter(UserHistory.user_id == user_id, UserHistory.session_id != None)\
    .group_by(UserHistory.session_id, UserHistory.title)\
    .order_by(desc('last_updated'))\
    .all()
    
    return [
        {
            "session_id": s.session_id, 
            "title": s.title or "Untitled Chat", 
            "last_updated": s.last_updated
        } 
        for s in sessions
    ]

@router.get("/history/{session_id}", response_model=List[UserHistoryResponse])
async def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    history = db.query(UserHistory)\
        .filter(UserHistory.user_id == current_user['user_id'], UserHistory.session_id == session_id)\
        .order_by(UserHistory.created_at.asc())\
        .all()
    
    return history