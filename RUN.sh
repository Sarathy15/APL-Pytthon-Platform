#!/bin/bash
# APL Migration Platform - Run Everything
# ============================================================

echo "======================================================================"
echo "APL Migration Platform - Full Stack Startup"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
fi

echo ""
echo -e "${BLUE}Step 1: Installing Backend Dependencies${NC}"
echo "============================================================"
if command -v pip &> /dev/null; then
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  pip not found. Please install Python dependencies manually:${NC}"
    echo "   pip install -r backend/requirements.txt"
fi

echo ""
echo -e "${BLUE}Step 2: Installing Frontend Dependencies${NC}"
echo "============================================================"
if command -v npm &> /dev/null; then
    npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  npm not found. Please install Node.js dependencies manually:${NC}"
    echo "   npm install"
fi

echo ""
echo -e "${BLUE}Step 3: Starting Backend Server${NC}"
echo "============================================================"
echo "Starting on port 8000..."
echo ""
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
cd ..

sleep 2

echo ""
echo -e "${BLUE}Step 4: Starting Frontend Server${NC}"
echo "============================================================"
echo "Starting on port 3000..."
echo ""
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

sleep 2

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ SYSTEM ONLINE${NC}"
echo "======================================================================"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo -e "  Frontend:   ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:    ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:   ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Mode:       ${YELLOW}$(grep '^AI_MODE=' .env | cut -d'=' -f2)${NC}"
echo -e "  Provider:   ${YELLOW}$(grep '^AI_PROVIDER=' .env | cut -d'=' -f2)${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

wait
