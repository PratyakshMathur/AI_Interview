from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Optional, Dict, Any

Base = declarative_base()

class Session(Base):
    """Interview session model"""
    __tablename__ = "sessions"
    
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_name = Column(String, nullable=False)
    interviewer_name = Column(String, nullable=True)
    problem_statement = Column(Text, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active")  # active, completed, terminated
    session_data = Column(JSON, default=dict)  # Additional session metadata
    
    # Relationships
    events = relationship("Event", back_populates="session", cascade="all, delete-orphan")
    ai_interactions = relationship("AIInteraction", back_populates="session", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="session", cascade="all, delete-orphan")

class Event(Base):
    """Behavioral event tracking model"""
    __tablename__ = "events"
    
    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False)  # SESSION_START, CODE_EDIT, AI_PROMPT, etc.
    event_metadata = Column(JSON, default=dict)  # Event-specific data
    sequence_number = Column(Integer, nullable=False)  # Order within session
    
    # Relationships
    session = relationship("Session", back_populates="events")

class AIInteraction(Base):
    """AI assistant interaction model"""
    __tablename__ = "ai_interactions"
    
    interaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    intent_label = Column(String, nullable=True)  # CONCEPT_HELP, DEBUG_HELP, etc.
    response_used = Column(Boolean, default=False)  # Did candidate use the response?
    context_data = Column(JSON, default=dict)  # Code context, error context, etc.
    
    # Relationships
    session = relationship("Session", back_populates="ai_interactions")

class Feature(Base):
    """Recruiter insight features model"""
    __tablename__ = "features"
    
    feature_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)
    feature_name = Column(String, nullable=False)  # Problem Understanding, Analytical Thinking, etc.
    feature_value = Column(Float, nullable=False)  # Computed score/rating
    confidence_score = Column(Float, default=0.0)  # Confidence in the measurement
    evidence = Column(JSON, default=list)  # Supporting events/interactions
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="features")

# Event type constants
EVENT_TYPES = [
    "SESSION_START",
    "CODE_EDIT", 
    "CODE_RUN",
    "RUN_RESULT",
    "ERROR_OCCURRED",
    "ERROR_RESOLVED",
    "DATA_VIEW",
    "AI_PROMPT",
    "AI_RESPONSE",
    "AI_RESPONSE_USED",
    "RESULT_EVALUATED",
    "IDLE_GAP"
]

# AI intent labels
AI_INTENT_LABELS = [
    "CONCEPT_HELP",
    "DEBUG_HELP", 
    "APPROACH_HELP",
    "VALIDATION",
    "DIRECT_SOLUTION",
    "EXPLANATION"
]

# Recruiter insight dimensions
FEATURE_DIMENSIONS = [
    "Problem Understanding",
    "Analytical Thinking",
    "Debugging Ability",
    "Independence vs AI Reliance",
    "Quality of AI Collaboration",
    "Iterative Thinking",
    "Code Quality",
    "Error Handling",
    "Data Exploration Skills",
    "Communication Clarity"
]