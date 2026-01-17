from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.sql import func
from typing import List, Optional
import os
import numpy as np
import google.generativeai as genai
from ..deps import get_db, get_current_user
from ..models import User, UserHistory, LearningPath
from ..schemas import UserHistoryCreate, UserHistoryResponse
from ..services.adaptive_engine import update_student_profile
from groq import Groq
import uuid

# ---------- Configuration / Constants ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Stable, free-tier friendly model names. Change these if you have access
GEMINI_PRIMARY_MODEL = "models/gemini-2.5-flash"
GEMINI_FALLBACK_MODEL = "models/gemini-2.0-flash"  # set to a different model if available
EMBEDDING_MODEL = "models/text-embedding-004"

# initialize SDKs
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not set. Gemini calls will fail.")

try:
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
    else:
        groq_client = None
        print("INFO: GROQ_API_KEY not set — Llama3 fallback disabled.")
except Exception as e:
    groq_client = None
    print(f"WARNING: Failed to initialize Groq client: {e}")

router = APIRouter(prefix="/chat", tags=["chat"]) 


# ---------- Utilities ----------

def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_embedding(text: str) -> List[float]:
    try:
        result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
        return result.get('embedding', [])
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []


def get_system_persona(learning_path: Optional[LearningPath], struggle_override: bool = False) -> str:
    if struggle_override:
        return (
            "SYSTEM OVERRIDE: ACTIVE RECALL MODE ENABLED.\n"
            "The user is stuck and repeating a question. They did not understand the previous explanation.\n"
            "RULES:\n"
            "1. Do NOT repeat the previous answer.\n"
            "2. Do NOT give the direct solution immediately.\n"
            "3. Use Socratic questions and scaffolding.\n"
            "4. Be empathetic but withhold full solution until understanding is checked."
        )

    if not learning_path:
        return "You are a helpful and clear computer science tutor."

    mode = getattr(learning_path, 'path_type', None)
    if mode == "Reinforcement":
        return "You are a supportive tutor. Use analogies and hints. Avoid full code answers."
    if mode == "Acceleration":
        return "You are a strict technical examiner. Be concise and challenge the student."
    return "You are a balanced tutor. Explain clearly."


# ---------- LLM calling logic (refactored) ----------

def _call_gemini_model(model_name: str, system_prompt: str, chat_history: List[dict], user_message: str) -> str:
    """Call Gemini via google.generativeai with a prepared history.
    Returns the text response or raises an exception if the call fails.
    """
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)

    gemini_history = []
    for msg in chat_history:
        gemini_history.append({"role": "user", "parts": [msg.get('prompt', '')]})
        gemini_history.append({"role": "model", "parts": [msg.get('response', '')]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(user_message)
    return response.text


def _call_groq_model(model_name: str, system_prompt: str, chat_history: List[dict], user_message: str) -> str:
    if not groq_client:
        raise RuntimeError("Groq client not configured")

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": "user", "content": msg.get('prompt', '')})
        messages.append({"role": "assistant", "content": msg.get('response', '')})
    messages.append({"role": "user", "content": user_message})

    chat_completion = groq_client.chat.completions.create(
        messages=messages,
        model=model_name,
    )
    return chat_completion.choices[0].message.content


def call_llm_service(system_prompt: str, chat_history: List[dict], user_message: str, model_choice: str = "gemini") -> str:
    """High-level LLM selector with robust fallbacks.

    Fallback order (for `model_choice == 'gemini'`):
      1) GEMINI_PRIMARY_MODEL
      2) GEMINI_FALLBACK_MODEL
      3) groq/llama3 (if configured)

    If `model_choice` is 'llama3' or 'deepseek', we route to Groq.
    """
    try:
        if model_choice == "llama3":
            return _call_groq_model("llama-3.1-8b-instant", system_prompt, chat_history, user_message)
        
        if model_choice == "deepseek":
            # Using DeepSeek R1 Distill Llama 70B via Groq
            return _call_groq_model("deepseek-r1-distill-llama-70b", system_prompt, chat_history, user_message)

        # Primary Gemini attempt
        try:
            return _call_gemini_model(GEMINI_PRIMARY_MODEL, system_prompt, chat_history, user_message)
        except Exception as gem_primary_exc:
            print(f"WARNING: Gemini primary model failed ({gem_primary_exc})")
            # If fallback model differs, try it once
            if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL != GEMINI_PRIMARY_MODEL:
                try:
                    return _call_gemini_model(GEMINI_FALLBACK_MODEL, system_prompt, chat_history, user_message)
                except Exception as gem_fallback_exc:
                    print(f"WARNING: Gemini fallback model also failed ({gem_fallback_exc})")

            # Try Groq/llama3 as a last resort
            if groq_client:
                try:
                    return _call_groq_model("llama-3.1-8b-instant", system_prompt, chat_history, user_message)
                except Exception as groq_exc:
                    print(f"WARNING: Groq fallback failed ({groq_exc})")

            # If we reach here, all real backends failed
            raise RuntimeError("All LLM backends failed for this request.")

    except Exception as e:
        print(f"CRITICAL LLM ERROR ({model_choice}): {e}")
        return "I'm having trouble thinking right now. Please try again later."


# ---------- FastAPI endpoints (unchanged behavior, cleaned)

@router.post("/message", response_model=UserHistoryResponse)
async def chat_with_ai(
    chat_request: UserHistoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user['user_id']
        prompt = chat_request.prompt
        session_id = chat_request.session_id or str(uuid.uuid4())
        selected_model = getattr(chat_request, 'model', 'gemini')

        title = None if chat_request.session_id else "New Chat"

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
                    if similarity > 0.70:
                        print("DEBUG: Struggle Detected!")
                        struggle_detected = True
                        break
        else:
            print("DEBUG: No current embedding or history found.")

        llm_input = prompt
        if struggle_detected:
            llm_input = (
                f"{prompt}\n\n"
                "[SYSTEM NOTE: The user has asked this exact question again. The previous answer failed. "
                "Do NOT repeat it. Ask guiding questions instead to test understanding.]"
            )

        system_persona = get_system_persona(learning_path, struggle_override=struggle_detected)

        ai_response = call_llm_service(system_persona, chat_history_list, llm_input, selected_model)

        # Auto-Title Generation using Groq (if new session)
        if (not chat_request.session_id or not recent_history) and not title:
             try:
                # Use Llama3 for cheap/fast titling if available, else Gemini
                title_model = "llama3" if groq_client else "gemini" 
                title_prompt = "Generate a very short, 3-5 word title for this chat based on the user's message. Do not use quotes."
                # Minimal call for title
                if title_model == "llama3":
                    generated_title = _call_groq_model("llama-3.1-8b-instant", title_prompt, [], prompt)
                else:
                    generated_title = _call_gemini_model(GEMINI_PRIMARY_MODEL, title_prompt, [], prompt)
                
                title = generated_title.strip().replace('"', '')
                print(f"Generated Title: {title}")
             except Exception as e:
                print(f"Title generation failed: {e}")
                title = "New Chat"

        new_interaction = UserHistory(
            user_id=user_id,
            session_id=session_id,
            title=title if title else "New Chat",
            prompt=prompt,
            response=ai_response,
            embedding_vector=current_embedding if current_embedding else [],
            telemetry_data=chat_request.telemetry_data
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
        UserHistory.user_id == current_user['user_id']
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
        {"session_id": s.session_id, "title": s.title or "Untitled Chat", "last_updated": s.last_updated}
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
    db.query(UserHistory).filter(
        UserHistory.session_id == session_id,
        UserHistory.user_id == current_user['user_id']
    ).delete()
    db.commit()
    return None
