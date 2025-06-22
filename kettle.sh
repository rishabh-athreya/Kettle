#!/bin/bash

# Kettle AI Daemon Script
# This script runs multiple services for the Kettle AI system

echo "🚀 Starting Kettle AI Services..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down Kettle AI services..."
    kill $FLASK_PID $MONITOR_PID $NEXTJS_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Flask API (background)
echo "📡 Starting Flask API..."
cd web_app/api
python app.py &
FLASK_PID=$!
cd ../..

# Start Kettle Monitor (background)
echo "👁️  Starting Kettle Monitor..."
python kettle_monitor.py &
MONITOR_PID=$!

# Start Next.js Frontend (background)
echo "🌐 Starting Next.js Frontend..."
cd web_app
npm run dev &
NEXTJS_PID=$!
cd ..

echo "✅ All services started!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait 