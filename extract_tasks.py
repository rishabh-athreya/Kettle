import json
from keys import PERPLEXITY_API_KEY
import requests

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def load_messages(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return [msg["text"] for msg in data.get("messages", [])]

def build_prompt(messages):
    joined = "\n".join(f"- {msg}" for msg in messages)
    return f"""
You will receive several Slack messages that describe requirements or requests for a *single software project*. These may come from different collaborators.

Your job is to:
1. Extract all **actionable coding tasks**
2. Categorize each task into one of the following project phases:
   - "project_setup" → creating folders, repos, or initializing environments
   - "dependency_installation" → installing libraries or tools
   - "feature_implementation" → coding functionality like routes, classes, logic, etc.

Return your output as a JSON list of objects. Each object must include:
- "task": a short description of what should be done
- "source": the Slack message it came from
- "phase": one of "project_setup", "dependency_installation", or "feature_implementation"

If a message contains multiple tasks, split them into separate entries.

Messages:
{joined}
"""

def call_perplexity(prompt):
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    response = requests.post(PERPLEXITY_API_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def main():
    messages = load_messages("messages.json")
    prompt = build_prompt(messages)
    output = call_perplexity(prompt)

    try:
        tasks = json.loads(output)

        with open("phased_tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)
        print("✅ Saved tasks to phased_tasks.json")

    except json.JSONDecodeError:
        print("❌ Perplexity returned invalid JSON:")
        print(output)

if __name__ == "__main__":
    main()
