import json
import requests
import os
from keys import ANTHROPIC_API_KEY
from prompts import extract_tasks_prompt

# Import dependency analyzer
import dependency_analyzer

# Use the modern messages endpoint
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# Parse out a clean JSON array of task objects
def extract_valid_tasks_json(response: str):
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "tasks" in data:
            return data["tasks"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Unexpected JSON structure")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}\nResponse was: {response}")
        return []

# Real Slack fetch - read from saved messages
def fetch_messages():
    try:
        with open("json/messages.json", "r") as f:
            data = json.load(f)
            messages = data.get("messages", [])
            
        # Get the last processed timestamp for tasks
        last_task_ts = 0
        try:
            with open("json/last_task_processed_ts.txt", "r") as f:
                last_task_ts = float(f.read().strip())
        except (FileNotFoundError, ValueError):
            pass
        
        # Check if we have any existing tasks
        try:
            with open("json/phased_tasks.json", "r") as f:
                existing_tasks = json.load(f)
                has_existing_tasks = len(existing_tasks) > 0
        except (FileNotFoundError, json.JSONDecodeError):
            has_existing_tasks = False
        
        # If no existing tasks, process all messages
        if not has_existing_tasks:
            print(f"Processing all {len(messages)} messages for initial task extraction")
            # Update the timestamp to the latest message processed
            if messages:
                latest_ts = max(float(msg.get("ts", 0)) for msg in messages)
                with open("json/last_task_processed_ts.txt", "w") as f:
                    f.write(str(latest_ts))
            return [msg.get("text", "") for msg in messages if msg.get("text", "").strip()]
        
        # Only process messages newer than the last task extraction
        new_messages = []
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts > last_task_ts:
                new_messages.append(msg.get("text", ""))
        
        if new_messages:
            print(f"Processing {len(new_messages)} new messages for task extraction")
            # Update the timestamp to the latest message processed
            latest_ts = max(float(msg.get("ts", 0)) for msg in messages)
            with open("json/last_task_processed_ts.txt", "w") as f:
                f.write(str(latest_ts))
            return new_messages
        else:
            print("No new messages for task extraction")
            return []
            
    except FileNotFoundError:
        print("Warning: json/messages.json not found. Using dummy message.")
        return ["Create a simple tic tac toe game to run on localhost"]
    except Exception as e:
        print(f"Error reading messages: {e}")
        return ["Create a simple tic tac toe game to run on localhost"]

# Call Claude via /v1/messages to enforce JSON output
def call_claude(prompt_text: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    # Build a system message that enforces JSON output
    system_message = (
        "You are a task extraction assistant. You must respond with ONLY valid JSON in the exact format specified. "
        "Do not include any explanatory text, markdown formatting, or additional commentary.\n\n"
        "RESPONSE FORMAT:\n"
        "Return a JSON array of task objects, where each task has:\n"
        "- \"task\": string\n"
        "- \"source\": string\n"
        "- \"phase\": string (project_setup, dependency_installation, feature_implementation)\n\n"
        "EXAMPLE RESPONSE:\n"
        "[\n"
        "  {\"task\": \"Create project directory structure\", \"source\": \"Create a web app\", \"phase\": \"project_setup\"},\n"
        "  {\"task\": \"Install Flask framework\", \"source\": \"Create a web app\", \"phase\": \"dependency_installation\"}\n"
        "]"
    )

    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8000,
        "system": system_message,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.1
    }

    print(f"Debug: Sending request to {ANTHROPIC_API_URL}")
    print(f"Debug: Headers: {headers}")
    print(f"Debug: Body keys: {list(body.keys())}")
    
    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    
    if resp.status_code != 200:
        print(f"Debug: Status code: {resp.status_code}")
        print(f"Debug: Response text: {resp.text}")
        resp.raise_for_status()

    # The `content` field contains the assistant's response
    return resp.json()["content"][0]["text"].strip()


def main():
    messages = fetch_messages()
    
    # Don't process tasks if there are no messages
    if not messages:
        print("No messages to process for task extraction")
        return
    
    prompt = extract_tasks_prompt(messages)
    raw = call_claude(prompt)
    tasks = extract_valid_tasks_json(raw)
    os.makedirs("json", exist_ok=True)
    with open("json/phased_tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)
    print(f"✅ Extracted {len(tasks)} tasks and wrote to json/phased_tasks.json")
    
    # Run dependency analysis on the extracted tasks
    print("🔍 Running dependency analysis...")
    dependency_analyzer.create_dependency_matrix(tasks)
    print("✅ Task extraction and dependency analysis complete")


if __name__ == "__main__":
    main()
