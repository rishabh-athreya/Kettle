import sys
import os

# Add the anthropic directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract_tasks
import execute

if __name__ == "__main__":
    print("🔵 Fetching Slack messages...")
    # Note: slack_fetch is the same for both versions, so we import from parent directory
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import slack_fetch
    slack_fetch.main()
    
    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()
    print("🟣 Executing project setup...")
    execute.main() 