#!/bin/bash

# Horyzonty Trip Planner - Full Stack Startup Script

echo "🌍 Starting Horyzonty Trip Planner..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Start backend
echo -e "${BLUE}📦 Starting FastAPI backend...${NC}"
cd backend
source ../venv/bin/activate 2>/dev/null || source ../venv/bin/activate.fish 2>/dev/null || echo "⚠️  Virtual environment not found"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
sleep 2
cd ..

# Start frontend
echo -e "${BLUE}⚛️  Starting React frontend...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
cd ..

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all background processes
wait $BACKEND_PID $FRONTEND_PID

