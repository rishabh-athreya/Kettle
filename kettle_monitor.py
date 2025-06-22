#!/usr/bin/env python3
"""
Kettle Monitor: Continuous Slack monitoring for web dashboard.
- Periodically checks Slack for new messages.
- Extracts tasks from new messages.
- Does NOT execute tasks automatically (web dashboard handles execution).
- Designed to work with the web dashboard architecture.
"""

import os
import sys
import time
import json
import subprocess
import signal
import psutil
from datetime import datetime
import threading
import queue
import requests
import slack_fetch
import extract_tasks
import json_utils

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class KettleMonitor:
    def __init__(self):
        self.slack_check_interval = 10.0  # seconds between Slack checks
        self.last_slack_check = 0
        self.last_processed_ts = 0
        
        # Load last processed timestamp (don't reset - run continuously)
        self.load_last_processed_ts()
        self.running = True

    def load_last_processed_ts(self):
        """Load the timestamp of the last processed message."""
        try:
            if os.path.exists("json/last_processed_ts.txt"):
                with open("json/last_processed_ts.txt", "r") as f:
                    self.last_processed_ts = float(f.read().strip())
        except (ValueError, FileNotFoundError):
            self.last_processed_ts = 0

    def check_slack_messages(self):
        """Checks Slack for new messages and extracts tasks."""
        current_time = time.time()
        
        # Throttle Slack API calls
        if current_time - self.last_slack_check < self.slack_check_interval:
            return

        print(f"🔍 Checking Slack for new messages... (last check: {time.strftime('%H:%M:%S', time.localtime(self.last_slack_check))})")
        
        # Fetch new messages
        try:
            print("🔄 Polling Slack for new messages...")
            slack_fetch.main()
            self.last_slack_check = current_time
        except Exception as e:
            print(f"❌ Error fetching Slack messages: {e}")
            return
        
        # Check for new messages since last processing
        try:
            with open("json/messages.json", "r") as f:
                messages = json.load(f).get("messages", [])
        except (IOError, json.JSONDecodeError):
            messages = []

        if not messages:
            print("📭 No messages found")
            return

        latest_ts = max(float(m.get("ts", 0)) for m in messages)

        if latest_ts > self.last_processed_ts:
            print(f"🆕 New messages detected! Processing {len([m for m in messages if float(m.get('ts', 0)) > self.last_processed_ts])} new messages...")
            
            # Extract tasks from new messages
            try:
                extract_tasks.main()
                print("✅ Tasks extracted successfully")
            except Exception as e:
                print(f"❌ Error extracting tasks: {e}")
                return
            
            # Run dependency analysis on all tasks (including new ones)
            try:
                # Load all tasks (including existing ones)
                with open("json/phased_tasks.json", "r") as f:
                    all_tasks = json.load(f)
                
                # Create dependency matrix for all tasks
                dependency_analyzer.create_dependency_matrix(all_tasks)
                print("✅ Dependency analysis completed")
            except Exception as e:
                print(f"⚠️  Error in dependency analysis: {e}")
            
            # Find similar projects (optional, for context)
            try:
                closest_project, similarity = project_matcher.main()
                if closest_project:
                    print(f"📁 Found similar project: {closest_project} (similarity: {similarity:.2f})")
            except Exception as e:
                print(f"⚠️  Error finding similar projects: {e}")
            
            # Update timestamp
            self.last_processed_ts = latest_ts
            with open("json/last_processed_ts.txt", "w") as f:
                f.write(str(self.last_processed_ts))
            
            print("✅ Processing complete - new tasks available in web dashboard")
        else:
            print("📭 No new messages since last check")

    def run(self):
        """Main monitoring loop."""
        print("🚀 Starting Kettle Monitor...")
        print("📊 Web dashboard should be running on http://localhost:3000")
        print("🔍 Monitoring Slack every 10 seconds...")
        print("⏹️  Press Ctrl+C to stop")
        
        try:
            while self.running:
                self.check_slack_messages()
                time.sleep(5)  # Check every 5 seconds, but throttle Slack API calls
        except KeyboardInterrupt:
            print("\n🛑 Stopping Kettle Monitor...")
            self.running = False

def main():
    monitor = KettleMonitor()
    monitor.run()

if __name__ == "__main__":
    main() 