# AIAI is AI-Assisted Interview Platform

An AI-powered behavioral interview platform for data roles that evaluates how candidates solve problems, not just final answers.

## 🎯 Overview

This MVP platform tracks candidate behavior during coding interviews and provides structured insights to recruiters about:
- Problem-solving approach
- AI collaboration skills  
- Debugging patterns
- Analytical thinking
- Independence vs AI reliance

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy + SQLite
- WebSockets for real-time updates
- Ollama for local AI integration

**Frontend:** 
- React with TypeScript
- TailwindCSS for styling
- Monaco Editor for coding
- Recharts for analytics visualization

**AI Assistant:**
- Local Ollama (Mistral/LLaMA)
- Controlled system prompts
- Intent classification

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies on macOS
brew install node python docker ollama

# Pull AI model
ollama pull mistral
```

### Development Setup

**1. Clone and setup backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Setup frontend:**
```bash
cd frontend
npm install
```

**3. Start services:**

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start backend
cd backend
python main.py

# Terminal 3: Start frontend  
cd frontend
npm start
```

**4. Open browser:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### Docker Deployment

```bash
# Start full stack
docker-compose up --build

# In another terminal, setup Ollama model
docker exec -it ai_interview_v1_ollama_1 ollama pull mistral
```

## 📊 How It Works

### 1. Session Flow
1. **Setup**: Candidate enters details and problem statement
2. **Interview**: Candidate codes with AI assistance in Monaco editor
3. **Tracking**: All interactions logged as behavioral events
4. **Analysis**: Events processed into 10 recruiter insight dimensions
5. **Dashboard**: Recruiters view behavioral analytics and evidence

### 2. Event Types Tracked
- `SESSION_START` - Interview begins
- `CODE_EDIT` - Code changes made
- `CODE_RUN` - Code execution attempts
- `ERROR_OCCURRED` / `ERROR_RESOLVED` - Debugging patterns
- `AI_PROMPT` / `AI_RESPONSE` - AI collaboration
- `DATA_VIEW` - Data exploration behavior
- `IDLE_GAP` - Thinking/pause patterns

### 3. Recruiter Insights
- **Problem Understanding** - How well they grasp requirements
- **Analytical Thinking** - Logical approach and hypothesis testing
- **Debugging Ability** - Error resolution patterns
- **Independence vs AI Reliance** - Balance of self-sufficiency
- **Quality of AI Collaboration** - Strategic vs random AI usage
- **Iterative Thinking** - Incremental improvement approach
- *Plus 4 additional dimensions*

## 💼 API Endpoints

**Sessions:**
- `POST /api/sessions` - Create interview session
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions/{id}/complete` - End session

**Events:**
- `POST /api/events` - Log behavioral event
- `GET /api/sessions/{id}/events` - Get session events

**AI Interactions:**
- `POST /api/ai/prompt` - Send AI prompt
- `POST /api/ai/response-used` - Mark response as used

**Analytics:**
- `GET /api/sessions/{id}/features` - Get computed insights

**WebSocket:**
- `WS /ws/{session_id}` - Real-time updates

## 🧑‍💻 Development Guide

### Adding New Event Types
1. Add event type to `models.py::EVENT_TYPES`
2. Implement tracking in `eventTracker.ts`
3. Add processing logic in `event_processor.py`

### Adding New Insight Dimensions
1. Add dimension to `models.py::FEATURE_DIMENSIONS`
2. Implement processor in `event_processor.py`
3. Update dashboard visualization

### AI Prompt Engineering
Modify system prompts in `ai_helper.py::_get_system_prompt()` to control AI behavior:
- Can explain concepts and guide thinking
- Cannot provide complete solutions
- Must encourage independent problem-solving

## 🔍 Testing

**Backend:**
```bash
cd backend
python -m pytest tests/
```

**Frontend:**
```bash
cd frontend
npm test
```

**Manual Testing:**
1. Create interview session
2. Write code with some errors
3. Ask AI for help multiple times
4. Run code several times
5. Complete session
6. Check recruiter dashboard for insights

## 📦 Database Schema

```sql
-- Core tables
sessions (session_id, candidate_name, problem_statement, start_time, status)
events (event_id, session_id, event_type, metadata, timestamp, sequence_number)
ai_interactions (interaction_id, session_id, user_prompt, ai_response, intent_label)
features (feature_id, session_id, feature_name, feature_value, evidence)
```

## 🚀 Deployment

**Production considerations:**
- Use PostgreSQL instead of SQLite
- Configure proper CORS and authentication
- Set up monitoring and logging
- Use production-grade AI model hosting
- Implement data backup and recovery

## 🐛 Known Issues

1. Code execution is currently mocked - integrate with real Python kernel
2. AI model needs to be pulled manually in Docker
3. Limited error handling for network issues
4. No user authentication implemented yet

## 📈 Future Enhancements

- Real code execution environment
- Video/audio recording integration
- Advanced AI prompt analysis
- Multi-language support
- Integration with ATS systems
- Advanced data visualizations
- ML model for insight accuracy

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

**Built with ❤️ for the future of AI-era hiring**
