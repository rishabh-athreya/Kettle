import os
import json
from keys import PERPLEXITY_API_KEY
import tempfile
import subprocess
import requests

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def load_phased_tasks(filepath="phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t["phase"]))

def build_prompt(sorted_tasks):
    task_list = "\n".join(
        f"- ({t['phase']}) {t['task']}" for t in sorted_tasks
    )
    return f"""
You are a coding assistant. Write a single Python script that performs the following project tasks in the correct order.
There are three categories of tasks:
project_setup – creating folders, files, or scaffolding
dependency_installation – installing Python packages (e.g. Flask, boto3)
feature_implementation – writing application code into files
🛠️ Requirements:
All project work must happen inside ~/Desktop/Work/<project-folder-name>
Use os.path.expanduser() to resolve the ~ path
Create the project folder before writing files
Set up a Python virtual environment inside the project folder
Use subprocess.run() to create the venv, install dependencies, etc.
✅ Your script must include all necessary imports (e.g. import os, import subprocess, import sys, etc.)
✅ Do not assume any modules are pre-imported
✅ The script must be runnable immediately without modification
Do not return explanations — only return valid, complete Python code
General Template Syntax Warning:
When generating code that involves templates, markup, or files that mix multiple languages (e.g., HTML with embedded template logic, CSS, or JavaScript):

- Only use the templating language's special delimiters (e.g., {{{{ ... }}}}, {{% ... %}} in Jinja2) for template logic or variable interpolation.
- For embedded languages (like CSS or JavaScript), use their standard syntax (e.g., single curly braces for CSS: body {{ background: #fff; }}).
- If you need to include literal template delimiters (such as {{{{ or }}}}), use the appropriate escaping mechanism (e.g., {{% raw %}} ... {{% endraw %}} in Jinja2).
- **Never use double curly braces or Jinja2 delimiters in CSS or JavaScript blocks unless you are intentionally inserting template logic.**
- If you are unsure, wrap CSS or JS blocks inside {{% raw %}} ... {{% endraw %}} to prevent Jinja2 from parsing them.
- Double-check that the generated code does not accidentally introduce syntax errors due to delimiter confusion.
Here are the tasks to perform:
{task_list}
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
    prompt = build_prompt(ordered_tasks)
    script = clean_code_blocks(call_perplexity(prompt))

    with open("script.py", "w") as f:
        f.write(script)
    print("✅ Generated script written to script.py")

    validate_script(script)
    execute_script(script)


if __name__ == "__main__":
    main()
