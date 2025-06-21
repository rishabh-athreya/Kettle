import sys
import os
import threading

# Add the anthropic directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract_tasks
import execute
import project_matcher
import dashboard

def run_main_pipeline():
    """Run the main Kettle pipeline"""
    print("🔵 Fetching Slack messages...")
    # Note: slack_fetch is the same for both versions, so we import from parent directory
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import slack_fetch
    slack_fetch.main()
    
    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()
    
    print("🟡 Finding similar existing projects...")
    closest_project, similarity = project_matcher.main()
    
    print("🟣 Executing project setup...")
    execute.main(existing_project_folder=closest_project)

def run_dashboard():
    """Run the dashboard widget in a separate thread"""
    print("📊 Starting Kettle dashboard widget...")
    dashboard.start_dashboard()

if __name__ == "__main__":
    # Run the main pipeline
    run_main_pipeline()
    
    # Start the dashboard widget in a separate thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    print("✅ Main pipeline completed. Dashboard widget is running in background.")
    print("💡 Click the ☕ widget at the bottom right to see latest work.") 