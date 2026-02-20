#!/bin/bash

# Proxmox VM Deployer - Startup Script
# Starts both backend and frontend in development mode

set -e

echo "🚀 Starting Proxmox VM Deployer..."
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo "Please copy backend/.env.example to backend/.env and configure it"
    exit 1
fi

# Create log directory
mkdir -p logs

# Start Backend
echo "📦 Starting Backend API..."
cd backend
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   Logs: logs/backend.log"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
cd ..

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check logs/backend.log"
        exit 1
    fi
    sleep 1
done

# Start Frontend
echo ""
echo "🎨 Starting Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "❌ Error: node_modules not found"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   Logs: logs/frontend.log"
cd ..

# Wait for frontend to be ready
echo ""
echo "⏳ Waiting for frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    sleep 1
done

# Save PIDs to file for cleanup
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

echo ""
echo "🎉 Proxmox VM Deployer is running!"
echo ""
echo "📍 Access the application:"
echo "   • Frontend: http://localhost:3001"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • Backend: tail -f logs/backend.log"
echo "   • Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo ""
