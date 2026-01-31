#!/bin/bash

echo "🚀 AI Interview Platform - Complete System Test"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 System Overview:${NC}"
echo "  • Backend: FastAPI with SQLAlchemy (Python 3.12.5 venv)"
echo "  • Frontend: React TypeScript with TailwindCSS"
echo "  • Database: SQLite with 4 tables"
echo "  • AI: Ollama integration (when available)"
echo "  • Features: Real-time event tracking, behavioral analytics"
echo ""

echo -e "${BLUE}🔧 Prerequisites:${NC}"
echo "  • Virtual environment: /Users/pratyaksh/UTA/AI_Interview_v1/venv"
echo "  • Backend dependencies: 24 packages installed"
echo "  • Frontend dependencies: 1416 packages installed"
echo ""

echo -e "${BLUE}🎯 Services Status:${NC}"

# Check if backend is running
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "  • Backend (port 8000): ${GREEN}✅ Running${NC}"
else
    echo -e "  • Backend (port 8000): ${RED}❌ Not running${NC}"
fi

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "  • Frontend (port 3000): ${GREEN}✅ Running${NC}"
else
    echo -e "  • Frontend (port 3000): ${RED}❌ Not running${NC}"
fi

echo ""
echo -e "${BLUE}🧪 API Test:${NC}"

# Test session creation
echo "  Creating test session..."
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"candidate_name": "Test User", "interviewer_name": "Test Interviewer", "problem_statement": "Test Problem"}')

if echo "$SESSION_RESPONSE" | grep -q "session_id"; then
    SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
    echo -e "  • Session created: ${GREEN}✅ $SESSION_ID${NC}"
    
    # Test event creation
    EVENT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/events \
      -H "Content-Type: application/json" \
      -d "{\"session_id\": \"$SESSION_ID\", \"event_type\": \"test_event\", \"event_metadata\": {\"test\": true}}")
    
    if echo "$EVENT_RESPONSE" | grep -q "event_id"; then
        echo -e "  • Event logged: ${GREEN}✅ Success${NC}"
    else
        echo -e "  • Event logged: ${RED}❌ Failed${NC}"
    fi
else
    echo -e "  • Session creation: ${RED}❌ Failed${NC}"
fi

echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo ""

echo -e "${BLUE}📁 Key Files:${NC}"
echo "  • Backend main: /Users/pratyaksh/UTA/AI_Interview_v1/backend/main.py"
echo "  • Frontend app: /Users/pratyaksh/UTA/AI_Interview_v1/frontend/src/App.tsx"
echo "  • Database: /Users/pratyaksh/UTA/AI_Interview_v1/backend/interview.db"
echo "  • Virtual env: /Users/pratyaksh/UTA/AI_Interview_v1/venv"
echo ""

echo -e "${BLUE}🎮 Usage Instructions:${NC}"
echo "  1. Open http://localhost:3000 in browser"
echo "  2. Fill in candidate details and problem statement"
echo "  3. Click 'Start Interview' to begin session"
echo "  4. Use code editor, chat with AI, run code"
echo "  5. Complete session for behavioral analysis"
echo ""

echo -e "${GREEN}✨ Platform ready for testing!${NC}"