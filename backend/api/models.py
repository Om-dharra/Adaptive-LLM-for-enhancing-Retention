from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import os


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    history = relationship("UserHistory", back_populates="user")
    skill_index = relationship("StudentSkillIndex", back_populates="user", uselist=False)
    learning_path = relationship("LearningPath", back_populates="user", uselist=False)
    quiz_scores = relationship("QuizScore", back_populates="user")
    telemetry = relationship("TelemetryLog", back_populates="user")
    dkt_state = relationship("DKTState", back_populates="user", uselist=False)

class UserHistory(Base):
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, index=True, nullable=True) # UUID for grouping
    title = Column(String, nullable=True) # Chat Title
    prompt = Column(String)
    response = Column(String)
    embedding_vector = Column(JSON, nullable=True) 
    telemetry_data = Column(JSON, nullable=True) # New Telemetry Column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="history")

class StudentSkillIndex(Base):
    __tablename__ = "student_skill_index"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    

    index_value = Column(Float, default=50.0) 
    

    bucket = Column(String, default="Moderate") 
    

    metrics_json = Column(JSON) 
    
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", back_populates="skill_index")

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    

    path_type = Column(String, default="Balanced") 
    
    current_difficulty = Column(Integer, default=1)
    
    ai_persona_mode = Column(String, default="Tutor") 
    
    user = relationship("User", back_populates="learning_path")

class QuizScore(Base):
    __tablename__ = "quiz_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    topic_tag = Column(String) # e.g., "Python Loops"
    score = Column(Float)      # e.g., 80.0
    total_questions = Column(Integer)
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="quiz_scores")

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String)
    
    event_type = Column(String) 
    
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="telemetry")


class DKTState(Base):
    __tablename__ = "dkt_states"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    skill_vector = Column(JSON) 
    
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="dkt_state")