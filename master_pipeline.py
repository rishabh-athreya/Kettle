import sys
import os

# Add the anthropic directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract_tasks
import project_matcher

def run_main_pipeline():
    """Run the main Kettle pipeline - fetch and extract only"""
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
    
    print("✅ Pipeline completed - tasks extracted and ready for selection in web dashboard")
    print("💡 Use the web dashboard to select and execute tasks manually")

if __name__ == "__main__":
    # Run the main pipeline (fetch and extract only)
    run_main_pipeline() 