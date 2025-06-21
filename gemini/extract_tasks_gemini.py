import json
from keys import GEMINI_API_KEY
import requests
from prompts import extract_tasks_prompt

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def load_messages(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return [msg["text"] for msg in data.get("messages", [])]

def call_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": GEMINI_API_KEY
    }
    body = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=body)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def strip_markdown_code_block(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove the first and last lines (the triple backticks)
        return "\n".join(lines[1:-1])
    return text

def main():
    messages = load_messages("json/messages.json")
    prompt = extract_tasks_prompt(messages)
    output = call_gemini(prompt)
    output = strip_markdown_code_block(output)

    try:
        tasks = json.loads(output)
        print(json.dumps(tasks, indent=2))

        with open("json/phased_tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)
        print("✅ Saved tasks to json/phased_tasks.json")

    except json.JSONDecodeError:
        print("❌ Gemini returned invalid JSON:")
        print(output)

if __name__ == "__main__":
    main() 