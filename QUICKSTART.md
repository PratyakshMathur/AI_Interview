# 🚀 Quick Start Guide

## Running the Application

### Option 1: One-Command Startup (Recommended)
```bash
./start.sh
```

This will:
- ✅ Kill any existing processes on ports 8000 and 3000
- ✅ Start the backend server (FastAPI on port 8000)
- ✅ Start the frontend server (React on port 3000)
- ✅ Automatically open http://localhost:3000 in your browser
- 📊 Show backend logs in real-time

**To stop:** Press `Ctrl+C` in the terminal

### Option 2: Clear Database and Restart
```bash
# Clear all test data
./clean_db.sh --clear-data

# Or reset database completely
./clean_db.sh --reset
```

---

### Option 2: Manual Startup

#### Backend:
```bash
cd backend
../venv/bin/python -c "import sys; sys.path.insert(0, '.'); import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)"
```

#### Frontend (in a new terminal):
```bash
cd frontend
npm start
```

---

## URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## Troubleshooting

### Clear Database

To clear all session data and start fresh:

```bash
# Option 1: Clear all data but keep schema (fast, no restart needed)
./clean_db.sh --clear-data

# Option 2: Delete and recreate database (requires backend restart)
./clean_db.sh
# or
./clean_db.sh --reset
```

**What's the difference?**
- `--clear-data`: Deletes all sessions/events/features but keeps the database tables. Backend continues running.
- `--reset`: Completely deletes the database file and recreates it. Backend needs restart.

### Port Already in Use
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Check Logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log
```

### Backend Won't Start
```bash
# Verify Python environment
source venv/bin/activate
python --version  # Should be 3.12.5

# Reinstall dependencies
cd backend
../venv/bin/pip install -r requirements.txt
```

### Frontend Won't Start
```bash
# Reinstall node modules
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## Development

### Making the startup script executable
```bash
chmod +x start.sh
```

### Running in development mode
The startup script runs both servers in reload mode:
- Backend: Auto-reloads on Python file changes
- Frontend: Auto-reloads on React file changes

---

## Features

✅ **Jupyter Notebook Interface**
- Toggle between Python and SQL
- Multiple cells with individual execution
- Inline output display
- Shift+Enter to run cells

✅ **VS Code Editor Mode**
- Classic single-file editor
- Terminal output panel
- Error display

✅ **AI Assistant**
- Context-aware help
- Problem-solving guidance
- Real-time behavioral tracking

✅ **Real Code Execution**
- Backend Python execution with pandas/numpy
- SQL queries on sample database
- Proper error handling
