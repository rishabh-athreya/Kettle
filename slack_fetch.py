import os
import json
from datetime import datetime, timezone, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# You can set these in your environment or in keys.py
try:
    from keys import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, BOT_USER_ID
except ImportError:
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")
    BOT_USER_ID = os.environ.get("BOT_USER_ID")

assert SLACK_BOT_TOKEN, "SLACK_BOT_TOKEN must be set in environment or keys.py"
assert SLACK_CHANNEL_ID, "SLACK_CHANNEL_ID must be set in environment or keys.py"

client = WebClient(token=SLACK_BOT_TOKEN)

# How many messages to fetch (adjust as needed)
MESSAGE_LIMIT = 50

# Option 2: Fetch bot user ID from Slack if not set
if not BOT_USER_ID:
    auth_resp = client.auth_test()
    BOT_USER_ID = auth_resp["user_id"]
    print(f"🤖 Bot user ID detected: {BOT_USER_ID}")

def fetch_recent_messages(channel_id, limit=MESSAGE_LIMIT):
    try:
        response = client.conversations_history(channel=channel_id, limit=limit)
        messages = response["messages"]
        return messages
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        return []

def messages_stale(messages, minutes=5):
    if not messages:
        return False
    latest_ts = float(messages[0]["ts"])
    latest_time = datetime.fromtimestamp(latest_ts, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - latest_time) > timedelta(minutes=minutes)

def get_last_processed_ts():
    try:
        with open("json/last_processed_ts.txt", "r") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_messages(messages, path="json/messages.json", since_ts=None):
    # Only keep messages not sent by the bot itself
    filtered = [m for m in messages if m.get("user") != BOT_USER_ID]
    if since_ts is not None:
        filtered = [m for m in filtered if float(m.get("ts", 0)) > float(since_ts)]
    
    # Load existing messages
    existing_messages = []
    try:
        with open(path, "r") as f:
            existing_data = json.load(f)
            existing_messages = existing_data.get("messages", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Combine existing and new messages, avoiding duplicates
    all_messages = existing_messages.copy()
    existing_ts = {msg.get("ts") for msg in existing_messages}
    
    for msg in filtered:
        if msg.get("ts") not in existing_ts:
            all_messages.append({
                "text": msg.get("text", ""), 
                "user": msg.get("user", ""), 
                "ts": msg.get("ts", "")
            })
    
    # Sort by timestamp (newest first)
    all_messages.sort(key=lambda x: float(x.get("ts", 0)), reverse=True)
    
    formatted = {"messages": all_messages}
    
    if len(filtered) > 0:
        with open(path, "w") as f:
            json.dump(formatted, f, indent=2)
        print(f"Saved {len(filtered)} new messages (total: {len(all_messages)})")
        
        # Update the last processed timestamp to the latest message
        if all_messages:
            latest_ts = float(all_messages[0]["ts"])
            with open("json/last_processed_ts.txt", "w") as f:
                f.write(str(latest_ts))
            print(f"Updated last processed timestamp to: {latest_ts}")
    else:
        print("No new messages, waiting to check again...")

def main():
    last_processed_ts = get_last_processed_ts()
    messages = fetch_recent_messages(SLACK_CHANNEL_ID)
    save_messages(messages, since_ts=last_processed_ts)

if __name__ == "__main__":
    main() 