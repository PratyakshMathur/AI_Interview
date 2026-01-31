#!/bin/bash

# AI Interview Platform Startup Script
# Run this from the project root directory

echo "🚀 Starting AI Interview Platform..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "venv" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Please run this script from the AI_Interview_v1 project root directory"
    exit 1
fi

echo -e "${BLUE}📋 Pre-flight checks...${NC}"

# Clear any existing processes on ports
echo "  • Clearing ports 8000 and 3000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

echo -e "${BLUE}🔧 Starting Backend Server...${NC}"

# Start backend in background
cd backend
source ../venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"
else
    echo -e "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${BLUE}🎨 Starting Frontend Server...${NC}"

# Start frontend
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 10

# Check if frontend started successfully
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend running on http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend starting... check http://localhost:3000 in a moment${NC}"
fi

echo ""
echo -e "${GREEN}🎉 AI Interview Platform is ready!${NC}"
echo ""
echo -e "${BLUE}📱 Access URLs:${NC}"
echo "  • Main Application: http://localhost:3000"
echo "  • API Documentation: http://localhost:8000/docs" 
echo "  • Backend Health: http://localhost:8000/health"
echo ""
echo -e "${BLUE}🛑 To stop the system:${NC}"
echo "  Press Ctrl+C to stop this script"
echo "  Or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${YELLOW}💡 Tip: The application will automatically open in your browser${NC}"

# Store PIDs for cleanup
echo $BACKEND_PID > .backend_pid
echo $FRONTEND_PID > .frontend_pid

# Wait for user to stop
trap 'echo -e "\n${BLUE}🛑 Shutting down...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; rm -f .backend_pid .frontend_pid; exit 0' INT

echo "Press Ctrl+C to stop the system..."
wait