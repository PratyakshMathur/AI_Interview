#!/bin/bash

# AI Interview Platform Startup Script
# This script starts both backend and frontend servers and opens the app in your browser

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting AI Interview Platform...${NC}\n"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kill existing processes on ports 8000 and 3000
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Setup Mistral AI
echo -e "${GREEN}🤖 Setting up Mistral AI...${NC}"

# Check if Ollama is installed
if ! command -v ollama > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama not found. Please install: https://ollama.ai/download${NC}"
    exit 1
fi

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${BLUE}🔄 Starting Ollama service...${NC}"
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
fi

# Check if Mistral model is available
if ! ollama list | grep -q "mistral"; then
    echo -e "${YELLOW}📥 Downloading Mistral model (4.4 GB)... This may take a few minutes.${NC}"
    ollama pull mistral
else
    echo -e "${GREEN}✅ Mistral model already available${NC}"
fi

# Verify Ollama is responding
echo -e "${BLUE}⏳ Verifying Mistral is ready...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Mistral AI ready on http://localhost:11434${NC}"
else
    echo -e "${RED}❌ Ollama service not responding${NC}"
    exit 1
fi

# Start Backend
echo -e "${GREEN}📦 Starting Backend Server...${NC}"
cd backend
../venv/bin/python -c "import sys; sys.path.insert(0, '.'); import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)" > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${BLUE}⏳ Waiting for backend to initialize...${NC}"
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Check /tmp/backend.log${NC}"
    exit 1
fi

# Start Frontend
echo -e "${GREEN}🎨 Starting Frontend Server...${NC}"
cd frontend
npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to compile
echo -e "${BLUE}⏳ Waiting for frontend to compile...${NC}"
sleep 8

# Check if frontend is running
if lsof -ti:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend running on http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend failed to start. Check /tmp/frontend.log${NC}"
    exit 1
fi

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 AI Interview Platform is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${BLUE}📍 URLs:${NC}"
echo -e "   Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "   Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "   API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "   Ollama AI: ${YELLOW}http://localhost:11434${NC}\n"

echo -e "${BLUE}🤖 AI Engine:${NC}"
echo -e "   Primary: Mistral (Ollama - Local)${NC}"
echo -e "   Fallback: Google Gemini 1.5 Flash${NC}\n"

echo -e "${BLUE}🔧 Process IDs:${NC}"
echo -e "   Backend PID: $BACKEND_PID"
echo -e "   Frontend PID: $FRONTEND_PID\n"

echo -e "${BLUE}📋 Logs:${NC}"
echo -e "   Backend:  /tmp/backend.log"
echo -e "   Frontend: /tmp/frontend.log"
echo -e "   Ollama:   /tmp/ollama.log\n"

echo -e "${YELLOW}💡 To stop: Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID${NC}\n"

# Open browser
echo -e "${BLUE}🌐 Opening browser...${NC}\n"
sleep 2
if command -v open > /dev/null; then
    open http://localhost:3000
elif command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
else
    echo -e "${YELLOW}⚠️  Could not auto-open browser. Please visit http://localhost:3000${NC}"
fi

# Keep script running and show logs
echo -e "${GREEN}📊 Showing backend logs (Ctrl+C to exit):${NC}\n"
tail -f /tmp/backend.log
