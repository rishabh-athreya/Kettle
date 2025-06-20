import os
import json
from keys import PERPLEXITY_API_KEY
import tempfile
import subprocess
import requests
from prompts import execute_tasks_prompt
from project_matcher import find_closest_project, save_project_embedding
import glob
import time
import re

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def load_phased_tasks(filepath="json/phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t["phase"]))

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

def gather_code_files(project_folder):
    print(f"[DEBUG] Gathering files from: {project_folder}")
    code_files = []
    for root, dirs, files in os.walk(os.path.expanduser(project_folder)):
        # Skip any venv directories
        dirs[:] = [d for d in dirs if d != "venv"]
        for file in files:
            if file.endswith(".py") or file.endswith(".json"):
                code_files.append(os.path.join(root, file))
    files_content = {}
    for f in code_files:
        try:
            with open(f, "r") as file:
                files_content[os.path.relpath(f, project_folder)] = file.read()
        except Exception as e:
            print(f"[DEBUG] Could not read {f}: {e}")
            continue
    print(f"[DEBUG] Total files gathered: {len(files_content)}")
    return files_content

def slugify(text):
    return re.sub(r'[^a-zA-Z0-9_]+', '_', text.strip().lower())[:30]

def get_latest_project_folder(work_dir="~/Desktop/Work"):
    work_dir = os.path.expanduser(work_dir)
    folders = [os.path.join(work_dir, d) for d in os.listdir(work_dir) if os.path.isdir(os.path.join(work_dir, d))]
    if not folders:
        return None
    latest_folder = max(folders, key=os.path.getmtime)
    return latest_folder

def main():
    tasks = load_phased_tasks()
    ordered_tasks = sort_tasks_by_phase(tasks)
    # Use the messages that generated the tasks for matching
    messages = [t["source"] for t in ordered_tasks]
    project_folder, score = find_closest_project(messages)
    codebase = None
    creating_new_project = False
    if project_folder:
        print(f"🔄 Modifying existing project at {project_folder} (similarity: {score:.2f})")
        # Gather all code files and send to LLM
        codebase = gather_code_files(project_folder)
        print(f"Sending {len(codebase)} files to LLM for modification.")
    else:
        # Use a human-readable project name from the first message
        first_message = messages[0] if messages else "project"
        project_name = slugify(first_message)
        project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")
        print(f"🆕 Creating new project at {project_folder}")
        creating_new_project = True
    prompt = execute_tasks_prompt(ordered_tasks, codebase=codebase)
    script = clean_code_blocks(call_perplexity(prompt))

    with open("script.py", "w") as f:
        f.write(script)
    print("✅ Generated script written to script.py")

    validate_script(script)
    execute_script(script)

    # After script runs, get the actual folder created/modified
    if creating_new_project:
        actual_folder = get_latest_project_folder()
        print(f"[DEBUG] Detected actual project folder: {actual_folder}")
        if actual_folder:
            save_project_embedding(actual_folder, messages)

if __name__ == "__main__":
    main()
