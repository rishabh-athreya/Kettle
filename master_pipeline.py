import os
import sys
import time
import json
import subprocess
import signal
import psutil
from datetime import datetime
import threading
from extract_tasks import *
from execute import *
from research_processor import *
from dependency_analyzer import *
from project_matcher import *
from json_utils import *

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def auto_reset():
    """Automatically reset all JSON files at the start of each new session"""
    print("🧹 Checking if auto-reset is needed...")
    
    # Check if this is a new session by looking for a session marker
    session_marker_file = "json/session_active.txt"
    current_time = time.time()
    
    try:
        # Check if session marker exists and is recent (within last 5 minutes)
        if os.path.exists(session_marker_file):
            with open(session_marker_file, "r") as f:
                last_session_time = float(f.read().strip())
            
            # If last session was more than 5 minutes ago, consider it a new session
            if current_time - last_session_time > 300:  # 5 minutes
                print("⏰ New session detected (last session was >5 minutes ago)")
                json_utils.clear_json_files()
                print("✅ System reset complete - ready for new session")
            else:
                print("🔄 Continuing existing session - no reset needed")
        else:
            # No session marker exists, this is a fresh start
            print("🆕 Fresh start detected - resetting system")
            json_utils.clear_json_files()
            print("✅ System reset complete - ready for new session")
        
        # Update session marker
        with open(session_marker_file, "w") as f:
            f.write(str(current_time))
            
    except Exception as e:
        print(f"⚠️  Warning: Could not complete auto-reset: {e}")
        print("   Continuing with existing data...")

def check_task_types():
    """Check what types of tasks are available in phased_tasks.json"""
    try:
        with open("json/phased_tasks.json", "r") as f:
            phased_tasks = json.load(f)
        
        task_types = {
            "coding": False,
            "research": False,
            "writing": False
        }
        
        if isinstance(phased_tasks, dict):
            if "coding" in phased_tasks and phased_tasks["coding"]:
                task_types["coding"] = True
            if "research" in phased_tasks and phased_tasks["research"]:
                task_types["research"] = True
            if "writing" in phased_tasks and phased_tasks["writing"]:
                task_types["writing"] = True
        
        return task_types
    except FileNotFoundError:
        print("📝 No phased_tasks.json found")
        return {"coding": False, "research": False, "writing": False}
    except Exception as e:
        print(f"❌ Error checking task types: {e}")
        return {"coding": False, "research": False, "writing": False}

def run_main_pipeline():
    """Run the main KettleAI pipeline"""
    print("🔵 Starting KettleAI Pipeline...")
    
    # Step 0: Auto-reset system for fresh start
    auto_reset()
    
    # Step 1: Extract tasks from messages (creates hierarchical tasks)
    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()
    
    # Step 2: Check what types of tasks we have
    print("🔍 Checking available task types...")
    task_types = check_task_types()
    
    print(f"📋 Available tasks:")
    print(f"   💻 Coding: {'Yes' if task_types['coding'] else 'No'}")
    print(f"   🔍 Research: {'Yes' if task_types['research'] else 'No'}")
    print(f"   ✍️  Writing: {'Yes' if task_types['writing'] else 'No'}")
    
    # Step 3: Execute coding tasks if available
    if task_types["coding"]:
        print("🟣 Executing coding tasks...")
        # Find similar existing projects
        print("🟡 Finding similar existing projects...")
        closest_project, similarity = project_matcher.main()
        
        if closest_project:
            print(f"   📁 Using existing project: {closest_project}")
            execute.main(existing_project_folder=closest_project)
        else:
            print("   🆕 Creating new project")
            execute.main()
    else:
        print("💻 No coding tasks found - skipping coding execution")
    
    # Step 4: Process research tasks (can be done independently)
    if task_types["research"]:
        print("🔍 Processing research tasks...")
        research_processor.main()
    else:
        print("🔍 No research tasks found - skipping research processing")
    
    # Step 5: Handle writing tasks (future enhancement)
    if task_types["writing"]:
        print("✍️  Writing tasks ready for manual processing")
        print("   💡 Writing tasks will be enhanced in future versions")
    else:
        print("✍️  No writing tasks found")
    
    print("✅ KettleAI pipeline completed!")

def run_dashboard():
    """Run the dashboard widget in a separate thread"""
    print("📊 Starting KettleAI dashboard...")
    try:
        # Start the web dashboard
        subprocess.run(["cd", "web_app", "&&", "npm", "run", "dev"], shell=True)
    except Exception as e:
        print(f"⚠️  Could not start dashboard: {e}")

if __name__ == "__main__":
    # Run the main pipeline
    run_main_pipeline()
    
    # Start the dashboard in a separate thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    print("✅ Main pipeline completed. Dashboard is running in background.")
    print("💡 Access the dashboard at http://localhost:3000") 