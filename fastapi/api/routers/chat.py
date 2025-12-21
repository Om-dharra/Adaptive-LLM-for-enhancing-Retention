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

import google.generativeai as genai
from groq import Groq
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
            "SYSTEM OVERRIDE: ACTIVE RECALL MODE ENABLED.\n"
            "The user is stuck in a loop and is repeating a question. They did not understand the previous explanation.\n"
            "RULES:\n"
            "1. DO NOT repeat your previous answer.\n"
            "2. DO NOT give the direct solution or definition immediately.\n"
            "3. Switch to 'Socratic Tutor' mode: Ask a simple, foundational question to check their understanding.\n"
            "4. Break the concept down into smaller steps (Scaffolding).\n"
            "5. Be empathetic but firm on not giving the answer yet."
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

def call_llm_service(system_prompt: str, chat_history: List[dict], user_message: str, model_choice: str = "gemini") -> str:
    """
    Calls the selected LLM service.
    For 'gemini', it implements a fail-safe mechanism: 
    Try 'gemini-1.5-pro' first -> if it fails (Rate Limit), fall back to 'gemini-1.5-flash'.
    """

    # Helper function to avoid rewriting the Gemini setup twice
    def _call_gemini_model(model_name: str):
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )
        
        gemini_history = []
        for msg in chat_history:
            gemini_history.append({"role": "user", "parts": [msg['prompt']]})
            gemini_history.append({"role": "model", "parts": [msg['response']]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text

    try:
        # --- OPTION 1: LLAMA 3 (GROQ) ---
        if model_choice == "llama3":
            messages = [{"role": "system", "content": system_prompt}]
            for msg in chat_history:
                messages.append({"role": "user", "content": msg['prompt']})
                messages.append({"role": "assistant", "content": msg['response']})
            messages.append({"role": "user", "content": user_message})

            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
            )
            return chat_completion.choices[0].message.content

        else:
            try:
                return _call_gemini_model("gemini-1.5-flash")
            
            except Exception as e:
                print(f"WARNING: Primary Gemini Pro model failed ({e}). Switching to Flash fallback...")
                return _call_gemini_model("gemini-1.5-flash")

    except Exception as e:
        print(f"CRITICAL LLM ERROR ({model_choice}): {e}")
        return f"I'm having trouble thinking with {model_choice} right now. Please try again."

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
        selected_model = getattr(chat_request, 'model', 'gemini')

        import uuid
        if not session_id:
            session_id = str(uuid.uuid4())
            title = "New Chat"  
        else:
            title = None

        learning_path = db.query(LearningPath).filter(LearningPath.user_id == user_id).first()
        
        history_limit = 5
        recent_history = db.query(UserHistory)\
            .filter(UserHistory.user_id == user_id, UserHistory.session_id == session_id)\
            .order_by(desc(UserHistory.created_at))\
            .limit(history_limit)\
            .all()
        
        chat_history_list = [{"prompt": h.prompt, "response": h.response} for h in reversed(recent_history)]
        current_embedding = get_embedding(prompt) 
        struggle_detected = False
        
        if current_embedding and recent_history:
            print(f"DEBUG: Checking {len(recent_history)} past messages for similarity...")
            for past_msg in recent_history:
                if past_msg.embedding_vector:
                    similarity = calculate_cosine_similarity(current_embedding, past_msg.embedding_vector)
                    print(f"DEBUG: Similarity with past msg: {similarity:.4f}")
                    
                    if similarity > 0.70: # Lowered from 0.85
                        print("DEBUG: Struggle Detected!")
                        struggle_detected = True
                        break   
        else:
             print("DEBUG: No current embedding or history found.")

        llm_input = prompt
        
        if struggle_detected:
 
            llm_input = (
                f"{prompt}\n\n"
                "[SYSTEM NOTE: The user has asked this exact question again. "
                "The previous answer failed. Do NOT repeat it. "
                "Ask a guiding question instead to test my understanding.]"
            )

        system_persona = get_system_persona(learning_path, struggle_override=struggle_detected)
        

        ai_response = call_llm_service(system_persona, chat_history_list, llm_input, selected_model)

        new_interaction = UserHistory(
            user_id=user_id,
            session_id=session_id,
            title=title if title else None,
            prompt=prompt, # Save original prompt
            response=ai_response,
            embedding_vector=current_embedding if current_embedding else [],
            telemetry_data=chat_request.telemetry_data # Save telemetry
        )
        
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)

        try:
             update_student_profile(user_id, db, session_id) 
        except Exception as e:
             print(f"Adaptive Engine Update Failed: {e}")
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
        func.max(UserHistory.title).label('title'), 
        func.max(UserHistory.created_at).label('last_updated')
    )\
    .filter(UserHistory.user_id == user_id, UserHistory.session_id != None)\
    .group_by(UserHistory.session_id)\
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

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Delete all messages for this session
    db.query(UserHistory).filter(
        UserHistory.session_id == session_id,
        UserHistory.user_id == current_user['user_id']
    ).delete()
    
    db.commit()
    return None