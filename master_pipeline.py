import slack_fetch
import extract_tasks
import execute

if __name__ == "__main__":
    print("🔵 Fetching Slack messages...")
    slack_fetch.main()
    print("🟢 Extracting tasks from messages...")
    extract_tasks.main()
    print("🟣 Executing project setup...")
    execute.main()