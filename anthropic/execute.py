import os
import json
from keys import ANTHROPIC_API_KEY
import tempfile
import subprocess
import requests
from prompts import execute_tasks_prompt

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def load_phased_tasks(filepath="json/phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t["phase"]))

def call_claude(prompt):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["content"][0]["text"]

def clean_code_blocks(response: str) -> str:
    if "```python" in response:
        return response.split("```python")[1].split("```")[0].strip()
    elif "```" in response:
        return response.split("```")[1].strip()
    return response.strip()

def execute_script(script_code):
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as f:
        f.write(script_code)
        temp_path = f.name

    print(f"\n🚀 Executing bootstrap script: {temp_path}")
    try:
        subprocess.run(["python3", temp_path], check=True)
        print("✅ Script executed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Script failed:", e)
    finally:
        os.remove(temp_path)
        print(f"🧹 Deleted temp file: {temp_path}")

def validate_script(script_code):
    required_imports = ["import os", "import subprocess", "import sys"]
    for imp in required_imports:
        if imp not in script_code:
            raise ValueError(f"🚨 Missing import: {imp}")

def main():
    tasks = load_phased_tasks()
    ordered_tasks = sort_tasks_by_phase(tasks)
    prompt = execute_tasks_prompt(ordered_tasks)
    script = clean_code_blocks(call_claude(prompt))

    with open("script.py", "w") as f:
        f.write(script)
    print("✅ Generated script written to script.py")

    validate_script(script)
    execute_script(script)


if __name__ == "__main__":
    main() 