#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PORT="${PORT:-8000}"

echo -e "${BLUE}Starting AI Recruiter Assistance Prototype...${NC}"

# 1. Build frontend (static files will be served by FastAPI backend)
echo -e "${GREEN}Building Frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

# 2. Start Backend (serves both API and frontend static files)
echo -e "${GREEN}Starting Backend API on port ${PORT}...${NC}"
python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
