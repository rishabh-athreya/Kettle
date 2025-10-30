import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import subprocess
import sys

# You can set these in your environment or in utils/keys.py
try:
    from utils.keys import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, BOT_USER_ID
except Exception:
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
    
    # Format messages for saving (new batch)
    new_batch = []
    for msg in filtered:
        new_batch.append({
            "text": msg.get("text", ""), 
            "user": msg.get("user", ""), 
            "ts": msg.get("ts", "")
        })
    
    # Load existing messages (append mode)
    try:
        with open(path, "r") as f:
            existing = json.load(f).get("messages", [])
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []
    
    # Merge and de-duplicate by ts (keep latest occurrence)
    combined_map = {m.get("ts", ""): m for m in existing if m.get("ts")}
    for m in new_batch:
        ts = m.get("ts")
        if ts:
            combined_map[ts] = m
    combined = list(combined_map.values())
    
    # Sort by timestamp (newest first)
    try:
        combined.sort(key=lambda x: float(x.get("ts", 0)), reverse=True)
    except Exception:
        pass
    
    # Create the complete messages structure
    formatted = {"messages": combined}
    
    # Save merged messages
    with open(path, "w") as f:
        json.dump(formatted, f, indent=2)
    
    print(f"Saved {len(new_batch)} new messages, total now {len(combined)} (append mode)")
    
    # Update the last processed timestamp to the latest message
    if combined:
        try:
            latest_ts = float(combined[0].get("ts", 0))
            with open("json/last_processed_ts.txt", "w") as f:
                f.write(str(latest_ts))
            print(f"Updated last processed timestamp to: {latest_ts}")
        except Exception:
            pass
    else:
        print("No messages found to save")

def main():
    print("🔍 Fetching messages from Slack...")
    messages = fetch_recent_messages(SLACK_CHANNEL_ID)
    save_messages(messages)

if __name__ == "__main__":
    main() 