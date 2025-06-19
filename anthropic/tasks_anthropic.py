import json
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

def load_messages(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return [msg["text"] for msg in data.get("messages", [])]

def build_prompt(sorted_tasks):
    task_list = "\n".join(
        f"- ({t['phase']}) {t['task']}" for t in sorted_tasks
    )
    return f"""
{HUMAN_PROMPT} You are a coding assistant. Write a single Python script that performs the following project tasks **in the correct order**.

There are three categories of tasks:
1. **project_setup** – creating folders, files, or scaffolding
2. **dependency_installation** – installing Python packages (e.g. Flask, boto3)
3. **feature_implementation** – writing application code into files

Requirements:
- All work must happen **inside a local project folder** (e.g. `image-uploader`)
- Use a **Python virtual environment** created inside that folder (e.g. `python3 -m venv venv`)
- Do **not** install any packages globally
- Use `subprocess.run()` or shell commands to:
  - Create the virtualenv
  - Install dependencies using the virtualenv’s `pip`
  - Create or modify Python files with necessary code
- Make sure any subprocess calls activate the venv properly

Here are the tasks to perform:

{task_list}

Return only valid Python code that performs these steps. No comments, no explanations.
{AI_PROMPT}
""".strip()

def call_claude(prompt):
    client = Anthropic()
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[HUMAN_PROMPT],
        model="claude-2.1",
        max_tokens_to_sample=800,
        temperature=0.3
    )
    return response.completion.strip()

def main():
    messages = load_messages("messages.json")
    prompt = build_prompt(messages)
    output = call_claude(prompt)

    # Validate JSON
    try:
        tasks = json.loads(output)
        print(json.dumps(tasks, indent=2))
    except json.JSONDecodeError:
        print("Claude returned invalid JSON:")
        print(output)

if __name__ == "__main__":
    main()
