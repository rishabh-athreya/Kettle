import os
import json
from datetime import datetime, timezone, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
import logging

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

# Fetch bot’s own user ID if not provided
if not BOT_USER_ID:
    auth_resp = client.auth_test()
    BOT_USER_ID = auth_resp["user_id"]
    print(f"🤖 Bot user ID detected: {BOT_USER_ID}")

logging.basicConfig(filename="slack_api.log", level=logging.INFO, format="%(asctime)s %(message)s")


def fetch_recent_messages(channel_id, since_ts=None, limit=50):
    params = {"channel": channel_id, "limit": limit}
    if since_ts:
        params["oldest"] = since_ts  # only messages newer than this

    while True:
        try:
            logging.info(f"conversations_history params={params}")
            response = client.conversations_history(**params)
            messages = response["messages"]
            # further filter out any that slipped through
            if since_ts:
                messages = [m for m in messages if float(m["ts"]) > float(since_ts)]
            return messages

        except SlackApiError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 1))
                logging.warning(f"[Slack] Rate limited; retry after {retry_after}s")
                time.sleep(retry_after + 0.5)
                continue
            logging.error(f"[Slack] API error: {e.response['error']}")
            raise


def messages_stale(messages, minutes=5):
    if not messages:
        return False
    latest_ts = float(messages[0]["ts"])
    latest_time = datetime.fromtimestamp(latest_ts, tz=timezone.utc)
    return (datetime.now(timezone.utc) - latest_time) > timedelta(minutes=minutes)


def save_messages(messages, path="json/messages.json", since_ts=None):
    # strip out bot’s own posts
    filtered = [m for m in messages if m.get("user") != BOT_USER_ID]
    if since_ts is not None:
        filtered = [
            m for m in filtered
            if m.get("ts") and float(m["ts"]) > float(since_ts)
        ]

    formatted = {
        "messages": [
            {"text": m.get("text",""), "user": m.get("user",""), "ts": m.get("ts","")}
            for m in filtered
        ]
    }
    with open(path, "w") as f:
        json.dump(formatted, f, indent=2)
    print(f"✅ Saved {len(filtered)} messages to {path}")


def main(since_ts=None):
    """
    Entry point for master_pipeline.py.
    Pass in since_ts so only new messages get written.
    """
    messages = fetch_recent_messages(SLACK_CHANNEL_ID, since_ts=since_ts, limit=50)
    if messages_stale(messages, minutes=5):
        save_messages(messages, path="json/messages.json", since_ts=since_ts)
    else:
        print("⏳ New messages detected in the last 5 minutes. Waiting...")


if __name__ == "__main__":
    # when run directly, just fetch all recent
    main()
