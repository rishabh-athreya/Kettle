import os
import json

import slack_fetch
import extract_tasks
import execute
import subprocess

if __name__ == "__main__":
    subprocess.Popen(["python3", "kettle_dashboard.py"])
    print("🔵 Fetching Slack messages...")
    slack_fetch.main()
    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()
    print("🟣 Executing project setup...")
    execute.main()
    print("🟠 Launching Kettle dashboard...")