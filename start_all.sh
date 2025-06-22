#!/bin/bash

# Start Continuous Slack Monitoring (waits until you exit)
echo "==============================="
echo "Starting: Slack Monitoring"
echo "==============================="
source kettle_env/bin/activate
python kettle_monitor.py

echo "==============================="
echo "Starting: Flask API"
echo "==============================="
cd web_app/api
../../kettle_env/bin/python app.py
cd ../..

echo "==============================="
echo "Starting: Next.js Frontend"
echo "==============================="
cd web_app
npm run dev
cd ..

echo "All services have finished running." 