#!/bin/bash

# Kettle Daemon Startup Script
echo "🚀 Starting Kettle Daemon..."
echo "📝 This will monitor VS Code and show the widget when it's open"
echo "💡 The widget will appear at the bottom right of your screen"
echo "🛑 Press Ctrl+C to stop the daemon"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment and start daemon
source venv/bin/activate
python kettle_daemon.py 