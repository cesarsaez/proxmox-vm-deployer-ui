#!/bin/bash

# Proxmox VM Deployer - Stop Script
# Stops both backend and frontend

echo "🛑 Stopping Proxmox VM Deployer..."
echo ""

# Stop Backend
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "📦 Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend process not found"
    fi
    rm -f logs/backend.pid
else
    echo "⚠️  No backend PID file found"
fi

# Stop Frontend
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🎨 Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "✅ Frontend stopped"
    else
        echo "⚠️  Frontend process not found"
    fi
    rm -f logs/frontend.pid
else
    echo "⚠️  No frontend PID file found"
fi

# Also kill any remaining uvicorn or vite processes (cleanup)
echo ""
echo "🧹 Cleaning up any remaining processes..."
pkill -f "uvicorn app.main:app" || true
pkill -f "vite" || true

echo ""
echo "✅ Proxmox VM Deployer stopped"
echo ""
