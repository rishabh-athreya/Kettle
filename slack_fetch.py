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

def save_messages(messages, path="json/messages.json", since_ts=None):
    # Only keep messages not sent by the bot itself
    filtered = [m for m in messages if m.get("user") != BOT_USER_ID]
    if since_ts is not None:
        filtered = [m for m in filtered if float(m.get("ts", 0)) > float(since_ts)]
    formatted = {"messages": [{"text": m.get("text", ""), "user": m.get("user", ""), "ts": m.get("ts", "")} for m in filtered]}
    with open(path, "w") as f:
        json.dump(formatted, f, indent=2)
    print(f"✅ Saved {len(filtered)} messages to {path} (excluding bot's own messages and before since_ts)")

def main():
    messages = fetch_recent_messages(SLACK_CHANNEL_ID)
    if messages_stale(messages, minutes=0.1):
        save_messages(messages)
    else:
        print("⏳ New messages detected in the last 5 minutes. Waiting...")

if __name__ == "__main__":
    main() 