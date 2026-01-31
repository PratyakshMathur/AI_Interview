#!/bin/bash

# AI Interview Platform - Real-Time Log Monitor
# This script shows real-time logs from all components

echo "🔍 AI Interview Platform - Real-Time Error Monitor"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to check if a log file exists
check_log_file() {
    if [ ! -f "$1" ]; then
        touch "$1"
        echo -e "${YELLOW}Created log file: $1${NC}"
    fi
}

# Create log directory if it doesn't exist
mkdir -p /Users/pratyaksh/UTA/AI_Interview_v1/logs

# Ensure log files exist
check_log_file "/Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log"
check_log_file "/Users/pratyaksh/UTA/AI_Interview_v1/logs/frontend.log"
check_log_file "/Users/pratyaksh/UTA/AI_Interview_v1/logs/system.log"

echo ""
echo -e "${BLUE}📋 Log File Locations:${NC}"
echo "  • Backend API: /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log"
echo "  • Frontend: Browser DevTools Console (F12)"
echo "  • System: /Users/pratyaksh/UTA/AI_Interview_v1/logs/system.log"
echo ""

echo -e "${BLUE}🎯 Monitoring Options:${NC}"
echo "  1. Watch backend logs only"
echo "  2. Watch all log files" 
echo "  3. Search for specific errors"
echo "  4. Show error summary"
echo "  q. Quit"
echo ""

read -p "Choose option (1-4, q): " choice

case $choice in
    1)
        echo -e "${GREEN}📊 Monitoring Backend Logs (Press Ctrl+C to stop)...${NC}"
        echo ""
        tail -f /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log | while read line; do
            if echo "$line" | grep -i "error" > /dev/null; then
                echo -e "${RED}ERROR: $line${NC}"
            elif echo "$line" | grep -i "warning" > /dev/null; then
                echo -e "${YELLOW}WARN:  $line${NC}"
            elif echo "$line" | grep -i "info" > /dev/null; then
                echo -e "${BLUE}INFO:  $line${NC}"
            else
                echo "$line"
            fi
        done
        ;;
    2)
        echo -e "${GREEN}📊 Monitoring All Logs (Press Ctrl+C to stop)...${NC}"
        echo ""
        (
            tail -f /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log 2>/dev/null | sed 's/^/[BACKEND] /' &
            tail -f /Users/pratyaksh/UTA/AI_Interview_v1/logs/system.log 2>/dev/null | sed 's/^/[SYSTEM]  /' &
            wait
        )
        ;;
    3)
        read -p "Enter search term (e.g., 'error', 'exception', '500'): " search_term
        echo -e "${GREEN}🔍 Searching for '$search_term' in logs...${NC}"
        echo ""
        echo -e "${PURPLE}=== Backend Logs ===${NC}"
        grep -i "$search_term" /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log 2>/dev/null | tail -10
        echo ""
        echo -e "${PURPLE}=== System Logs ===${NC}"
        grep -i "$search_term" /Users/pratyaksh/UTA/AI_Interview_v1/logs/system.log 2>/dev/null | tail -10
        ;;
    4)
        echo -e "${GREEN}📈 Error Summary (Last 50 lines)...${NC}"
        echo ""
        echo -e "${RED}=== ERRORS ===${NC}"
        grep -i "error" /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log 2>/dev/null | tail -10
        echo ""
        echo -e "${YELLOW}=== WARNINGS ===${NC}"
        grep -i "warning" /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log 2>/dev/null | tail -10
        echo ""
        echo -e "${BLUE}=== RECENT REQUESTS ===${NC}"
        grep "POST\|GET\|PUT\|DELETE" /Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log 2>/dev/null | tail -5
        ;;
    q)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option. Please choose 1-4 or q."
        ;;
esac

echo ""
echo -e "${BLUE}💡 Pro Tips:${NC}"
echo "  • For frontend errors: Open browser DevTools (F12) → Console tab"
echo "  • For network errors: DevTools → Network tab → filter by status codes"
echo "  • For React errors: Check browser console for component stack traces"
echo "  • For backend API errors: Check the log file above or terminal output"