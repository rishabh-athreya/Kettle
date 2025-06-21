import os
import json
import time
import subprocess
from datetime import datetime, timezone
from slack_fetch import fetch_recent_messages, save_messages, SLACK_CHANNEL_ID

def reset_json_files():
    json_dir = "json"
    empty_defaults = {
        "messages.json": {"messages": []},
        "phased_tasks.json": [],
        "project_embeddings.json": {},
        "last_processed_ts.txt": ""
    }
    for fname, empty_val in empty_defaults.items():
        fpath = os.path.join(json_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "w") as f:
                if fname.endswith(".json"):
                    json.dump(empty_val, f, indent=2)
                else:
                    f.write(empty_val)
    print(f"[RESET] json/")

LAST_TS_PATH = os.path.join("json", "last_processed_ts.txt")
MESSAGES_PATH = os.path.join("json", "messages.json")
INACTIVITY_MINUTES = 0.33
POLL_INTERVAL = 10  # seconds


def load_last_processed_ts():
    if os.path.exists(LAST_TS_PATH):
        with open(LAST_TS_PATH, "r") as f:
            return f.read().strip()
    return None

def save_last_processed_ts(ts):
    with open(LAST_TS_PATH, "w") as f:
        f.write(str(ts))

def get_new_messages(since_ts=None):
    messages = fetch_recent_messages(SLACK_CHANNEL_ID, limit=100)
    # Only keep messages after since_ts
    if since_ts:
        messages = [m for m in messages if float(m["ts"]) > float(since_ts)]
    return messages

def main():
    reset_json_files()
    print("[Kettle Daemon] Starting background monitoring...")
    last_processed_ts = load_last_processed_ts()
    last_seen_ts = last_processed_ts
    idle_start = None

    while True:
        messages = get_new_messages(last_processed_ts)
        if messages:
            messages.sort(key=lambda m: float(m["ts"]), reverse=True)
            latest_ts = messages[0]["ts"]
            if last_seen_ts != latest_ts:
                last_seen_ts = latest_ts
                idle_start = datetime.now(timezone.utc)
                save_messages(messages, path=MESSAGES_PATH)
                print("[Kettle Daemon] New messages detected. Waiting for inactivity...")
            else:
                print("[Kettle Daemon] No truly new messages. Waiting for inactivity...")
        else:
            print("[Kettle Daemon] No messages found. Waiting...")

        # Check for inactivity
        if idle_start and (datetime.now(timezone.utc) - idle_start).total_seconds() >= INACTIVITY_MINUTES * 60:
            print("[Kettle Daemon] Inactivity detected. Processing batch...")
            subprocess.run(["python3", "master_pipeline.py"])
            save_last_processed_ts(last_seen_ts)
            last_processed_ts = last_seen_ts
            idle_start = None

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main() 