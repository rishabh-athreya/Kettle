import json
from keys import PERPLEXITY_API_KEY
import requests
from prompts import extract_tasks_prompt

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def load_messages(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return [msg["text"] for msg in data.get("messages", [])]

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
    messages = load_messages("json/messages.json")
    prompt = extract_tasks_prompt(messages)
    output = call_perplexity(prompt)

    try:
        tasks = json.loads(output)
        print(json.dumps(tasks, indent=2))

        with open("json/phased_tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)
        print("✅ Saved tasks to json/phased_tasks.json")

    except json.JSONDecodeError:
        print("❌ Perplexity returned invalid JSON:")
        print(output)

if __name__ == "__main__":
    main()
