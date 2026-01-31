#!/bin/bash

# Database Cleanup Script for AI Interview Platform
# This script provides options to clear or reset the database

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DB_PATH="$SCRIPT_DIR/backend/ai_interview.db"

echo -e "${BLUE}🗄️  AI Interview Platform - Database Cleanup${NC}\n"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${YELLOW}⚠️  No database file found at: $DB_PATH${NC}"
    echo -e "${GREEN}✓ Database will be created automatically when backend starts${NC}"
    exit 0
fi

# Show current database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo -e "Current database: ${YELLOW}$DB_PATH${NC}"
echo -e "Database size: ${YELLOW}$DB_SIZE${NC}\n"

# Check if running with argument
if [ "$1" == "--clear-data" ]; then
    # Clear data only (keep schema)
    echo -e "${YELLOW}📋 Clearing all data (keeping schema)...${NC}"
    
    sqlite3 "$DB_PATH" <<EOF
DELETE FROM features;
DELETE FROM ai_interactions;
DELETE FROM events;
DELETE FROM sessions;
VACUUM;
EOF
    
    echo -e "${GREEN}✅ All session data cleared!${NC}"
    echo -e "${BLUE}ℹ️  Database schema preserved${NC}"
    echo -e "${BLUE}ℹ️  Backend restart not required${NC}\n"
    
elif [ "$1" == "--reset" ] || [ "$1" == "" ]; then
    # Delete and recreate database
    echo -e "${YELLOW}🔄 Resetting database (delete and recreate)...${NC}"
    
    # Check if backend is running
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Backend is running on port 8000${NC}"
        read -p "Stop backend and continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}🛑 Stopping backend...${NC}"
            lsof -ti:8000 | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            echo -e "${RED}❌ Operation cancelled${NC}"
            exit 1
        fi
    fi
    
    # Delete database
    rm "$DB_PATH"
    echo -e "${GREEN}✅ Database deleted${NC}"
    echo -e "${BLUE}ℹ️  New database will be created on backend startup${NC}\n"
    
    # Ask if user wants to restart backend
    read -p "Restart backend now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🚀 Starting backend...${NC}"
        cd "$SCRIPT_DIR/backend"
        ../venv/bin/python -c "import sys; sys.path.insert(0, '.'); import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)" > /tmp/backend.log 2>&1 &
        BACKEND_PID=$!
        sleep 3
        
        if lsof -ti:8000 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend restarted (PID: $BACKEND_PID)${NC}"
            echo -e "${BLUE}📍 Backend: http://localhost:8000${NC}\n"
        else
            echo -e "${RED}❌ Backend failed to start. Check /tmp/backend.log${NC}"
        fi
    fi
    
else
    echo -e "${RED}❌ Invalid option: $1${NC}\n"
    echo -e "Usage:"
    echo -e "  ${GREEN}./clean_db.sh${NC}              - Reset database (delete & recreate)"
    echo -e "  ${GREEN}./clean_db.sh --reset${NC}      - Reset database (delete & recreate)"
    echo -e "  ${GREEN}./clean_db.sh --clear-data${NC} - Clear all data (keep schema)"
    echo -e ""
    echo -e "Examples:"
    echo -e "  ${BLUE}# Delete database and recreate (requires backend restart)${NC}"
    echo -e "  ./clean_db.sh"
    echo -e ""
    echo -e "  ${BLUE}# Clear all sessions but keep schema (no restart needed)${NC}"
    echo -e "  ./clean_db.sh --clear-data"
    exit 1
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Database cleanup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
