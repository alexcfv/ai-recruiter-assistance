#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting AI Recruiter Assistance Prototype...${NC}"

# 1. Backend
echo -e "${GREEN}Starting Backend API...${NC}"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Frontend
echo -e "${GREEN}Building and starting Frontend...${NC}"
cd frontend

if [ ! -d "node_modules/serve" ]; then
    echo "Installing 'serve' for production frontend..."
    npm install serve
fi

npm install
npm run build

npx serve -s dist -l 5173 &
FRONTEND_PID=$!

echo -e "${BLUE}All services started!${NC}"
echo -e "Backend: http://localhost:8000"
echo -e "Frontend: http://localhost:5173"
echo -e "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
