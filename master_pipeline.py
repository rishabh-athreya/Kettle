import slack_fetch
import extract_tasks
import execute
import subprocess
from kettle_daemon import load_last_processed_ts

if __name__ == "__main__":
    print("🔵 Fetching Slack messages...")
    # Pass in last_processed_ts so slack_fetch only writes the new ones
    last_ts = load_last_processed_ts()
    slack_fetch.main(since_ts=last_ts)

    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()

    print("🟣 Executing project setup...")
    execute.main()

    print("🟠 Launching Kettle dashboard...")
    subprocess.Popen(["python3", "kettle_dashboard.py"])
