from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class StudentSkillIndexBase(BaseModel):
    index_value: float = Field(..., ge=0, le=100, description="Composite score 0-100")
    bucket: str = Field(..., description="Weak, Moderate, or Strong")
    metrics_json: Dict[str, Any] = Field(default_factory=dict, description="Detailed sub-metrics like Retention Rate")

class LearningPathBase(BaseModel):
    path_type: str = Field(..., description="Reinforcement, Balanced, or Acceleration")
    current_difficulty: int = Field(default=1, ge=1)
    ai_persona_mode: str = Field(default="Tutor", description="Tutor, Socratic, or Examiner")

class TelemetryLogBase(BaseModel):
    session_id: str
    event_type: str = Field(..., description="Copy, Paste, TabSwitch, Hesitation")
    latency_ms: int

class QuizScoreBase(BaseModel):
    topic_tag: str
    score: float
    total_questions: int
    attempts: int = 1

class UserHistoryBase(BaseModel):
    prompt: str
    response: str
    session_id: Optional[str] = None
    title: Optional[str] = None


class TelemetryCreate(TelemetryLogBase):
    pass

class QuizScoreCreate(QuizScoreBase):
    pass

class UserHistoryCreate(BaseModel):
    prompt: str
    session_id: Optional[str] = None

class StudentSkillIndexResponse(StudentSkillIndexBase):
    id: int
    last_updated: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class LearningPathResponse(LearningPathBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class TelemetryResponse(TelemetryLogBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class QuizScoreResponse(QuizScoreBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserHistoryResponse(UserHistoryBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DKTStateResponse(BaseModel):
    id: int
    skill_vector: Optional[List[float]] = None 
    last_update: datetime

    model_config = ConfigDict(from_attributes=True)



class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    skill_index: Optional[StudentSkillIndexResponse] = None
    learning_path: Optional[LearningPathResponse] = None
    
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class QuestionOption(BaseModel):
    id: str  # e.g., "A", "B", "C", "D"
    text: str

class QuizQuestion(BaseModel):
    id: int
    question_text: str
    options: List[QuestionOption]
    correct_option_id: str
    explanation: str  # For feedback after they answer

class GeneratedQuiz(BaseModel):
    topic: str
    questions: List[QuizQuestion]