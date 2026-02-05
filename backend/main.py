from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from database import get_db, init_database
from models import Session as SessionModel, Event, AIInteraction, Feature
from pydantic import BaseModel
from ai_helper import AIHelper
from event_processor import EventProcessor
from code_executor import CodeExecutor
from sql_executor import SQLExecutor
from problem_manager.data_loader import load_problem_to_duckdb, get_problem_table_names
from langchain_config import init_ai_engine
from ai_analyzer import get_analyzer

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

# Initialize AI engine FIRST (before AIHelper)
import os
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    ai_engine = init_ai_engine(gemini_api_key=gemini_key)
    active_model = ai_engine.get_active_model_name() if ai_engine else "Unknown"
    logger.info(f"✅ AI Engine initialized with {active_model}")
else:
    ai_engine = init_ai_engine()  # Try without Gemini (Ollama only)
    if ai_engine and ai_engine.models:
        active_model = ai_engine.get_active_model_name()
        logger.info(f"✅ AI Engine initialized with {active_model}")
    else:
        logger.warning("⚠️  No AI models available - AI features will be limited")

# Initialize components (AIHelper needs AI engine to be ready)
ai_helper = AIHelper()
event_processor = EventProcessor()
code_executor = CodeExecutor(timeout=30)
# Session-specific SQL executors
sql_executors: Dict[str, SQLExecutor] = {}

# Pydantic models for request/response
class SessionCreate(BaseModel):
    candidate_name: str
    interviewer_name: Optional[str] = None
    problem_statement: str  # Can be empty if problem_id is provided
    problem_id: Optional[int] = None  # NEW: Reference to problem in problems.db
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
    session_id: Optional[str] = None

class CodeExecutionResponse(BaseModel):
    success: bool
    output: str
    error: str
    rows: Optional[List[Dict[str, Any]]] = None
    column_names: Optional[List[str]] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None

class SessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    interviewer_name: Optional[str]
    problem_statement: str
    problem_id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    phase: Optional[str] = "coding"  # NEW
    submitted_at: Optional[datetime] = None  # NEW
    ai_insights: Optional[Dict[str, Any]] = None  # NEW
    
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

# Problem API endpoints
PROBLEMS_DB_PATH = Path(__file__).parent / "problems.db"

def get_problems_db():
    """Get connection to problems database"""
    if not PROBLEMS_DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Problems database not found. Run problem_manager/init_db.py")
    return sqlite3.connect(PROBLEMS_DB_PATH)


def get_problem_context(problem_id: int) -> Optional[Dict[str, Any]]:
    """Get problem context for AI prompts"""
    try:
        conn = get_problems_db()
        cursor = conn.cursor()
        
        # Get problem details
        cursor.execute("""
            SELECT id, title, description, difficulty
            FROM problems
            WHERE id = ?
        """, (problem_id,))
        
        problem_row = cursor.fetchone()
        if not problem_row:
            conn.close()
            return None
        
        # Get table details
        cursor.execute("""
            SELECT table_name, schema_json
            FROM problem_tables
            WHERE problem_id = ?
            ORDER BY table_name
        """, (problem_id,))
        
        tables = []
        for row in cursor.fetchall():
            table_name, schema_json = row
            schema = json.loads(schema_json)
            
            # Count rows
            cursor.execute("""
                SELECT COUNT(*)
                FROM table_data
                WHERE problem_id = ? AND table_name = ?
            """, (problem_id, table_name))
            row_count = cursor.fetchone()[0]
            
            tables.append({
                "name": table_name,
                "schema": schema,
                "row_count": row_count
            })
        
        conn.close()
        
        return {
            "id": problem_row[0],
            "title": problem_row[1],
            "description": problem_row[2],
            "difficulty": problem_row[3],
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Error fetching problem context: {e}")
        return None

@app.get("/api/problems")
async def get_all_problems():
    """Get all available interview problems"""
    try:
        conn = get_problems_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.title, p.description, p.difficulty, p.created_at,
                   COUNT(DISTINCT pt.table_name) as table_count
            FROM problems p
            LEFT JOIN problem_tables pt ON p.id = pt.problem_id
            GROUP BY p.id
            ORDER BY p.id
        """)
        
        problems = []
        for row in cursor.fetchall():
            problems.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "difficulty": row[3],
                "created_at": row[4],
                "table_count": row[5]
            })
        
        conn.close()
        return problems
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching problems: {str(e)}")

@app.get("/api/problems/{problem_id}")
async def get_problem(problem_id: int):
    """Get specific problem with table details"""
    try:
        conn = get_problems_db()
        cursor = conn.cursor()
        
        # Get problem details
        cursor.execute("""
            SELECT id, title, description, difficulty, created_at
            FROM problems
            WHERE id = ?
        """, (problem_id,))
        
        problem_row = cursor.fetchone()
        if not problem_row:
            raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found")
        
        # Get table details
        cursor.execute("""
            SELECT table_name, schema_json
            FROM problem_tables
            WHERE problem_id = ?
            ORDER BY table_name
        """, (problem_id,))
        
        tables = []
        for table_name, schema_json in cursor.fetchall():
            schema = json.loads(schema_json)
            
            # Count rows
            cursor.execute("""
                SELECT COUNT(*)
                FROM table_data
                WHERE problem_id = ? AND table_name = ?
            """, (problem_id, table_name))
            row_count = cursor.fetchone()[0]
            
            tables.append({
                "name": table_name,
                "schema": schema,
                "row_count": row_count
            })
        
        conn.close()
        
        return {
            "id": problem_row[0],
            "title": problem_row[1],
            "description": problem_row[2],
            "difficulty": problem_row[3],
            "created_at": problem_row[4],
            "tables": tables
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching problem: {str(e)}")

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
            "problem_id": s.problem_id,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "status": s.status,
            "phase": s.phase,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "ai_insights": s.ai_insights
        } for s in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new interview session"""
    try:
        # If problem_id provided, fetch problem details from problems.db
        problem_statement = session_data.problem_statement
        problem_id = session_data.problem_id
        
        if problem_id:
            conn = get_problems_db()
            cursor = conn.cursor()
            cursor.execute("SELECT title, description FROM problems WHERE id = ?", (problem_id,))
            problem = cursor.fetchone()
            conn.close()
            
            if not problem:
                raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found")
            
            # Use problem description as problem_statement
            problem_statement = problem[1]  # description
        
        new_session = SessionModel(
            candidate_name=session_data.candidate_name,
            interviewer_name=session_data.interviewer_name,
            problem_statement=problem_statement,
            problem_id=problem_id,
            session_data=session_data.session_data
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        # Log session start event
        start_event = Event(
            session_id=new_session.session_id,
            event_type="SESSION_START",
            event_metadata={"candidate_name": session_data.candidate_name, "problem_id": problem_id},
            sequence_number=1
        )
        db.add(start_event)
        db.commit()
        
        return SessionResponse(
            session_id=new_session.session_id,
            candidate_name=new_session.candidate_name,
            interviewer_name=new_session.interviewer_name,
            problem_statement=new_session.problem_statement,
            problem_id=new_session.problem_id,
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
        problem_id=session.problem_id,
        start_time=session.start_time,
        end_time=session.end_time,
        status=session.status,
        phase=session.phase,
        submitted_at=session.submitted_at,
        ai_insights=session.ai_insights
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
        # Get mode from context_data (default to 'coding')
        mode = request.context_data.get('mode', 'coding') if request.context_data else 'coding'
        
        # Get session to retrieve problem_id
        session = db.query(SessionModel).filter(SessionModel.session_id == request.session_id).first()
        problem_context = None
        if session and session.problem_id:
            problem_context = get_problem_context(session.problem_id)
        
        # Get AI response with mode support and problem context
        ai_response = await ai_helper.process_prompt(
            request.user_prompt, 
            request.context_data,
            request.session_id,
            mode=mode,
            problem_context=problem_context
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
        
        # Get next sequence number
        last_event = db.query(Event).filter(
            Event.session_id == request.session_id
        ).order_by(Event.sequence_number.desc()).first()
        next_seq = (last_event.sequence_number + 1) if last_event else 1
        
        # Log appropriate events based on mode
        if mode == 'interview':
            # Interview mode events
            prompt_event = Event(
                session_id=request.session_id,
                event_type="INTERVIEW_ANSWER",
                event_metadata={
                    "answer": request.user_prompt,
                    "interaction_id": interaction.interaction_id
                },
                sequence_number=next_seq
            )
            db.add(prompt_event)
            
            # Check if we should complete the interview (after 5 Q&A pairs)
            interview_questions = db.query(Event).filter(
                Event.session_id == request.session_id,
                Event.event_type == "INTERVIEW_QUESTION"
            ).count()
            
            should_complete = interview_questions >= 5
            
            if should_complete:
                # Mark interview as complete instead of asking another question
                ai_response = "Thank you for your thoughtful responses! The interview is now complete. Your session will be available for review."
                
                response_event = Event(
                    session_id=request.session_id,
                    event_type="INTERVIEW_COMPLETED",
                    event_metadata={
                        "message": ai_response,
                        "total_questions": interview_questions,
                        "interaction_id": interaction.interaction_id
                    },
                    sequence_number=next_seq + 1
                )
                db.add(response_event)
                
                # Update session phase
                session = db.query(SessionModel).filter(SessionModel.session_id == request.session_id).first()
                if session:
                    session.phase = "completed"
                    session.end_time = datetime.utcnow()
            else:
                response_event = Event(
                    session_id=request.session_id,
                    event_type="INTERVIEW_QUESTION", 
                    event_metadata={
                        "question": ai_response,
                        "question_number": interview_questions + 1,
                        "interaction_id": interaction.interaction_id
                    },
                    sequence_number=next_seq + 1
                )
                db.add(response_event)
        else:
            # Coding mode events
            prompt_event = Event(
                session_id=request.session_id,
                event_type="AI_PROMPT",
                event_metadata={
                    "prompt": request.user_prompt,
                    "intent": intent,
                    "interaction_id": interaction.interaction_id
                },
                sequence_number=next_seq
            )
            db.add(prompt_event)
            
            response_event = Event(
                session_id=request.session_id,
                event_type="AI_RESPONSE", 
                event_metadata={
                    "response": ai_response,
                    "intent": intent,
                    "interaction_id": interaction.interaction_id
                },
                sequence_number=next_seq + 1
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
    
    # Get next sequence number
    last_event = db.query(Event).filter(
        Event.session_id == interaction.session_id
    ).order_by(Event.sequence_number.desc()).first()
    next_seq = (last_event.sequence_number + 1) if last_event else 1
    
    # Log usage event
    usage_event = Event(
        session_id=interaction.session_id,
        event_type="AI_RESPONSE_USED",
        event_metadata={"interaction_id": interaction_id},
        sequence_number=next_seq
    )
    db.add(usage_event)
    
    db.commit()
    return {"message": "Response marked as used"}

# ===== NEW: Phase Submission & Interview Endpoints =====

@app.post("/api/sessions/{session_id}/submit")
async def submit_coding_phase(session_id: str, db: Session = Depends(get_db)):
    """Submit coding phase and transition to interview mode"""
    try:
        # Get session
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.phase != "coding":
            raise HTTPException(status_code=400, detail=f"Cannot submit from phase: {session.phase}")
        
        # Update session
        session.phase = "interview"
        session.submitted_at = datetime.utcnow()
        
        # Get next sequence number
        last_event = db.query(Event).filter(
            Event.session_id == session_id
        ).order_by(Event.sequence_number.desc()).first()
        next_seq = (last_event.sequence_number + 1) if last_event else 1
        
        # Log phase submission event
        event = Event(
            session_id=session_id,
            event_type="PHASE_SUBMITTED",
            event_metadata={"timestamp": datetime.utcnow().isoformat()},
            sequence_number=next_seq
        )
        db.add(event)
        
        # Log interview started event
        interview_event = Event(
            session_id=session_id,
            event_type="INTERVIEW_STARTED",
            event_metadata={"timestamp": datetime.utcnow().isoformat()},
            sequence_number=next_seq + 1
        )
        db.add(interview_event)
        
        db.commit()
        
        # Get problem context for interview question generation
        problem_context = None
        if session.problem_id:
            problem_context = get_problem_context(session.problem_id)
        
        # Get SQL query history for context
        sql_queries = db.query(Event).filter(
            Event.session_id == session_id,
            Event.event_type == "SQL_RUN"
        ).all()
        query_history = [
            e.event_metadata.get('query', '') 
            for e in sql_queries 
            if e.event_metadata and e.event_metadata.get('query')
        ]
        
        # Generate first interview question using AI with problem context
        first_question = await ai_helper.generate_interview_question(
            session_id=session_id,
            query_history=query_history,
            question_number=1,
            problem_context=problem_context
        )
        
        # Log interview question
        question_event = Event(
            session_id=session_id,
            event_type="INTERVIEW_QUESTION",
            event_metadata={
                "question": first_question,
                "question_number": 1
            },
            sequence_number=next_seq + 2
        )
        db.add(question_event)
        db.commit()
        
        return {
            "phase": "interview",
            "message": "Coding phase submitted successfully",
            "first_question": first_question
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Submit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/analyze")
async def analyze_session(session_id: str, db: Session = Depends(get_db)):
    """Trigger AI analysis of session (for recruiter dashboard)"""
    try:
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Run analyzer AI
        analyzer = get_analyzer()
        insights = await analyzer.analyze_session(session_id, db)
        
        # Store insights in session
        session.ai_insights = insights
        db.commit()
        
        return insights
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def execute_sql_code(request: CodeExecutionRequest, db: Session = Depends(get_db)):
    """Execute SQL query with DuckDB"""
    try:
        # Get or create session-specific SQL executor
        session_id = request.session_id or "default"
        
        if session_id not in sql_executors:
            # Fetch session to get problem_id
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            
            if session and session.problem_id:
                # Get allowed tables for this problem
                allowed_tables = get_problem_table_names(session.problem_id)
                
                # Create executor with problem context
                executor = SQLExecutor(
                    session_id=session_id,
                    problem_id=session.problem_id,
                    allowed_tables=allowed_tables
                )
                
                # Load problem data into DuckDB
                load_problem_to_duckdb(session.problem_id, executor.conn)
                
                sql_executors[session_id] = executor
            else:
                # Fallback: no problem_id (legacy mode)
                sql_executors[session_id] = SQLExecutor(session_id=session_id)
        
        executor = sql_executors[session_id]
        success, rows, column_names, execution_time, error = executor.execute_query(request.code)
        
        # Log SQL_RUN event if session_id provided
        if request.session_id and success:
            try:
                # Get next sequence number
                last_event = db.query(Event).filter(
                    Event.session_id == request.session_id
                ).order_by(Event.sequence_number.desc()).first()
                next_sequence = (last_event.sequence_number + 1) if last_event else 1
                
                sql_event = Event(
                    session_id=request.session_id,
                    event_type="SQL_RUN",
                    event_metadata={
                        "query_text": request.code,
                        "execution_time": execution_time,
                        "row_count": len(rows),
                        "success": True
                    },
                    sequence_number=next_sequence
                )
                db.add(sql_event)
                db.commit()
            except Exception as log_error:
                logger.error(f"Failed to log SQL_RUN event: {log_error}")
        
        # Log errors
        if request.session_id and not success:
            try:
                last_event = db.query(Event).filter(
                    Event.session_id == request.session_id
                ).order_by(Event.sequence_number.desc()).first()
                next_sequence = (last_event.sequence_number + 1) if last_event else 1
                
                error_event = Event(
                    session_id=request.session_id,
                    event_type="SQL_RUN",
                    event_metadata={
                        "query_text": request.code,
                        "execution_time": execution_time,
                        "success": False,
                        "error_message": error
                    },
                    sequence_number=next_sequence
                )
                db.add(error_event)
                db.commit()
            except Exception as log_error:
                logger.error(f"Failed to log SQL error event: {log_error}")
        
        # Format output message for display
        output_msg = ""
        if success and rows:
            output_msg = f"Query executed successfully. {len(rows)} row(s) returned in {execution_time:.3f}s"
        elif success:
            output_msg = f"Query executed successfully in {execution_time:.3f}s"
        
        return CodeExecutionResponse(
            success=success,
            output=output_msg,
            error=error,
            rows=rows if success else None,
            column_names=column_names if success else None,
            execution_time=execution_time,
            row_count=len(rows) if success else None
        )
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return CodeExecutionResponse(
            success=False,
            output="",
            error=f"Execution error: {str(e)}",
            rows=None,
            column_names=None,
            execution_time=0.0,
            row_count=0
        )

# Get database schema endpoint
@app.get("/api/database-schema")
async def get_database_schema(session_id: Optional[str] = None):
    """Get database schema information"""
    try:
        # Get or create session-specific SQL executor
        sid = session_id or "default"
        if sid not in sql_executors:
            sql_executors[sid] = SQLExecutor(session_id=sid)
        
        schema = sql_executors[sid].get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schema: {str(e)}")

# Get sample data code for Python
@app.get("/api/sample-data-code")
async def get_sample_data_code():
    """Get Python code to load sample data"""
    from data_loader import SAMPLE_DATA_CODE
    return {"code": SAMPLE_DATA_CODE}

# ===== Notebook Save/Load Endpoints =====

class NotebookSaveRequest(BaseModel):
    session_id: str
    cells: List[Dict[str, Any]]

@app.post("/api/notebooks/{session_id}/save")
async def save_notebook(session_id: str, request: NotebookSaveRequest, db: Session = Depends(get_db)):
    """Save notebook state for a session"""
    try:
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save notebook data
        session.notebook_data = {
            "cells": request.cells,
            "saved_at": datetime.utcnow().isoformat()
        }
        db.commit()
        
        logger.info(f"Saved notebook for session {session_id} with {len(request.cells)} cells")
        return {"success": True, "message": f"Saved {len(request.cells)} cells"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notebooks/{session_id}/load")
async def load_notebook(session_id: str, db: Session = Depends(get_db)):
    """Load saved notebook state for a session"""
    try:
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        notebook_data = session.notebook_data
        if not notebook_data:
            # Return empty/default notebook if none saved
            return {
                "cells": [],
                "saved_at": None
            }
        
        logger.info(f"Loaded notebook for session {session_id}")
        return notebook_data
    except Exception as e:
        logger.error(f"Error loading notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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