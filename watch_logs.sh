#!/bin/bash

# Backend Log Monitor - Real-time error tracking
echo "🔍 Backend Log Monitor - Real-time"
echo "================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

LOG_FILE="/Users/pratyaksh/UTA/AI_Interview_v1/backend/app.log"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠️  Log file doesn't exist yet. Creating...${NC}"
    touch "$LOG_FILE"
    echo -e "${GREEN}✅ Log file created. Waiting for backend to start...${NC}"
fi

echo -e "${BLUE}📊 Monitoring: $LOG_FILE${NC}"
echo -e "${BLUE}📋 Legend:${NC}"
echo -e "  ${RED}🔴 ERROR${NC} - Application errors, exceptions"
echo -e "  ${YELLOW}🟡 WARN${NC}  - Warnings, non-critical issues"
echo -e "  ${GREEN}🟢 INFO${NC}  - Normal operations, API requests"
echo -e "  ${CYAN}🔵 SQL${NC}   - Database operations"
echo -e "  ${PURPLE}🟣 API${NC}   - HTTP requests/responses"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop monitoring...${NC}"
echo ""

# Monitor logs with real-time filtering and coloring
tail -f "$LOG_FILE" | while IFS= read -r line; do
    timestamp=$(date '+%H:%M:%S')
    
    if echo "$line" | grep -qi "error\|exception\|failed\|traceback"; then
        echo -e "${RED}🔴 [$timestamp] $line${NC}"
    elif echo "$line" | grep -qi "warning\|warn"; then
        echo -e "${YELLOW}🟡 [$timestamp] $line${NC}"
    elif echo "$line" | grep -qi "POST\|GET\|PUT\|DELETE.*HTTP"; then
        echo -e "${PURPLE}🟣 [$timestamp] $line${NC}"
    elif echo "$line" | grep -qi "sqlalchemy\|BEGIN\|COMMIT\|INSERT\|SELECT"; then
        echo -e "${CYAN}🔵 [$timestamp] $line${NC}"
    elif echo "$line" | grep -qi "info\|startup\|shutdown"; then
        echo -e "${GREEN}🟢 [$timestamp] $line${NC}"
    else
        echo -e "${NC}   [$timestamp] $line${NC}"
    fi
done