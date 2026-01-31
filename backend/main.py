from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import uuid
import logging
import sys

from database import get_db, init_database
from models import Session as SessionModel, Event, AIInteraction, Feature
from pydantic import BaseModel
from ai_helper import AIHelper
from event_processor import EventProcessor
from code_executor import CodeExecutor

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Platform API",
    description="Backend API for AI-powered behavioral interview platform",
    version="1.0.0"
)

# Error handling middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"{request.method} {request.url} - ERROR: {str(e)} - {process_time:.3f}s")
        raise

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ai_helper = AIHelper()
event_processor = EventProcessor()

# Import code executor
from code_executor import CodeExecutor
from sql_executor import SQLExecutor
code_executor = CodeExecutor(timeout=30)
sql_executor = SQLExecutor()

# Pydantic models for request/response
class SessionCreate(BaseModel):
    candidate_name: str
    interviewer_name: Optional[str] = None
    problem_statement: str
    session_data: Optional[Dict[str, Any]] = {}

class EventCreate(BaseModel):
    session_id: str
    event_type: str
    event_metadata: Optional[Dict[str, Any]] = {}

class AIPromptRequest(BaseModel):
    session_id: str
    user_prompt: str
    context_data: Optional[Dict[str, Any]] = {}

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"

class CodeExecutionResponse(BaseModel):
    success: bool
    output: str
    error: str

class SessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    interviewer_name: Optional[str]
    problem_statement: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    
class EventResponse(BaseModel):
    event_id: str
    session_id: str
    timestamp: datetime
    event_type: str
    event_metadata: Dict[str, Any]
    sequence_number: int

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        self.active_connections.remove(websocket)
        if session_id in self.session_connections:
            self.session_connections[session_id].remove(websocket)
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.session_connections:
            for connection in self.session_connections[session_id]:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# Initialize database on import
try:
    init_database()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")

# Session endpoints
@app.get("/api/sessions")
async def get_all_sessions(db: Session = Depends(get_db)):
    """Get all interview sessions"""
    try:
        sessions = db.query(SessionModel).order_by(SessionModel.start_time.desc()).all()
        return [{
            "session_id": s.session_id,
            "candidate_name": s.candidate_name,
            "interviewer_name": s.interviewer_name,
            "problem_statement": s.problem_statement,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "status": s.status
        } for s in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new interview session"""
    try:
        new_session = SessionModel(
            candidate_name=session_data.candidate_name,
            interviewer_name=session_data.interviewer_name,
            problem_statement=session_data.problem_statement,
            session_data=session_data.session_data
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        # Log session start event
        start_event = Event(
            session_id=new_session.session_id,
            event_type="SESSION_START",
            event_metadata={"candidate_name": session_data.candidate_name},
            sequence_number=1
        )
        db.add(start_event)
        db.commit()
        
        return SessionResponse(
            session_id=new_session.session_id,
            candidate_name=new_session.candidate_name,
            interviewer_name=new_session.interviewer_name,
            problem_statement=new_session.problem_statement,
            start_time=new_session.start_time,
            end_time=new_session.end_time,
            status=new_session.status
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.post("/api/execute-python", response_model=CodeExecutionResponse)
async def execute_python_code(request: CodeExecutionRequest):
    """Execute Python code in a sandboxed environment"""
    try:
        logger.info(f"Executing Python code ({len(request.code)} chars)")
        
        success, stdout, stderr = code_executor.execute_python(request.code)
        
        logger.info(f"Execution completed - Success: {success}")
        
        return CodeExecutionResponse(
            success=success,
            output=stdout,
            error=stderr
        )
        
    except Exception as e:
        logger.error(f"Python execution error: {e}")
        return CodeExecutionResponse(
            success=False,
            output="",
            error=f"Server error: {str(e)}"
        )

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session by ID"""
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session.session_id,
        candidate_name=session.candidate_name,
        interviewer_name=session.interviewer_name,
        problem_statement=session.problem_statement,
        start_time=session.start_time,
        end_time=session.end_time,
        status=session.status
    )

@app.post("/api/sessions/{session_id}/complete")
async def complete_session(session_id: str, db: Session = Depends(get_db)):
    """Complete an interview session"""
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.status = "completed"
    session.end_time = datetime.utcnow()
    
    # Trigger feature computation
    await event_processor.compute_features(session_id, db)
    
    db.commit()
    return {"message": "Session completed successfully"}

# Event endpoints
@app.post("/api/events", response_model=EventResponse)
async def log_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Log a behavioral event"""
    try:
        # Get next sequence number
        last_event = db.query(Event).filter(
            Event.session_id == event_data.session_id
        ).order_by(Event.sequence_number.desc()).first()
        
        next_sequence = (last_event.sequence_number + 1) if last_event else 1
        
        new_event = Event(
            session_id=event_data.session_id,
            event_type=event_data.event_type,
            event_metadata=event_data.event_metadata,
            sequence_number=next_sequence
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        # Send real-time update
        await manager.send_to_session(event_data.session_id, {
            "type": "event_logged",
            "event": {
                "event_id": new_event.event_id,
                "event_type": new_event.event_type,
                "timestamp": new_event.timestamp.isoformat(),
                "metadata": new_event.event_metadata
            }
        })
        
        return EventResponse(
            event_id=new_event.event_id,
            session_id=new_event.session_id,
            timestamp=new_event.timestamp,
            event_type=new_event.event_type,
            event_metadata=new_event.event_metadata,
            sequence_number=new_event.sequence_number
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging event: {str(e)}")

@app.get("/api/sessions/{session_id}/events")
async def get_session_events(session_id: str, db: Session = Depends(get_db)):
    """Get all events for a session"""
    events = db.query(Event).filter(
        Event.session_id == session_id
    ).order_by(Event.sequence_number).all()
    
    return [{
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "metadata": event.event_metadata,
        "sequence_number": event.sequence_number
    } for event in events]

# AI interaction endpoints
@app.post("/api/ai/prompt")
async def ai_prompt(request: AIPromptRequest, db: Session = Depends(get_db)):
    """Send prompt to AI assistant"""
    try:
        # Get AI response
        ai_response = await ai_helper.process_prompt(
            request.user_prompt, 
            request.context_data
        )
        
        # Classify intent
        intent = ai_helper.classify_intent(request.user_prompt)
        
        # Store interaction
        interaction = AIInteraction(
            session_id=request.session_id,
            user_prompt=request.user_prompt,
            ai_response=ai_response,
            intent_label=intent,
            context_data=request.context_data
        )
        db.add(interaction)
        
        # Log AI_PROMPT and AI_RESPONSE events
        prompt_event = Event(
            session_id=request.session_id,
            event_type="AI_PROMPT",
            event_metadata={
                "prompt": request.user_prompt,
                "intent": intent,
                "interaction_id": interaction.interaction_id
            }
        )
        db.add(prompt_event)
        
        response_event = Event(
            session_id=request.session_id,
            event_type="AI_RESPONSE", 
            event_metadata={
                "response": ai_response,
                "intent": intent,
                "interaction_id": interaction.interaction_id
            }
        )
        db.add(response_event)
        
        db.commit()
        
        return {
            "interaction_id": interaction.interaction_id,
            "response": ai_response,
            "intent": intent
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing AI prompt: {str(e)}")

@app.post("/api/ai/response-used")
async def mark_response_used(interaction_id: str, db: Session = Depends(get_db)):
    """Mark AI response as used by candidate"""
    interaction = db.query(AIInteraction).filter(
        AIInteraction.interaction_id == interaction_id
    ).first()
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    interaction.response_used = True
    
    # Log usage event
    usage_event = Event(
        session_id=interaction.session_id,
        event_type="AI_RESPONSE_USED",
        event_metadata={"interaction_id": interaction_id}
    )
    db.add(usage_event)
    
    db.commit()
    return {"message": "Response marked as used"}

# Features endpoint
@app.get("/api/sessions/{session_id}/features")
async def get_session_features(session_id: str, db: Session = Depends(get_db)):
    """Get computed behavioral features for a session"""
    features = db.query(Feature).filter(
        Feature.session_id == session_id
    ).all()
    
    return [{
        "feature_name": feature.feature_name,
        "feature_value": feature.feature_value,
        "confidence_score": feature.confidence_score,
        "evidence": feature.evidence,
        "computed_at": feature.computed_at.isoformat()
    } for feature in features]

# SQL execution endpoint
@app.post("/api/execute-sql", response_model=CodeExecutionResponse)
async def execute_sql_code(request: CodeExecutionRequest):
    """Execute SQL query"""
    try:
        success, output, error = sql_executor.execute_query(request.code)
        return CodeExecutionResponse(
            success=success,
            output=output,
            error=error
        )
    except Exception as e:
        return CodeExecutionResponse(
            success=False,
            output="",
            error=f"Execution error: {str(e)}"
        )

# Get database schema endpoint
@app.get("/api/database-schema")
async def get_database_schema():
    """Get database schema information"""
    try:
        schema = sql_executor.get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schema: {str(e)}")

# Get sample data code for Python
@app.get("/api/sample-data-code")
async def get_sample_data_code():
    """Get Python code to load sample data"""
    from data_loader import SAMPLE_DATA_CODE
    return {"code": SAMPLE_DATA_CODE}

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can add real-time processing
            await manager.send_to_session(session_id, {
                "type": "echo",
                "data": data
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)