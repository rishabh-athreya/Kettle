import os
import json
from keys import PERPLEXITY_API_KEY
import tempfile
import subprocess
import requests
from prompts import execute_tasks_prompt
from project_manager import ProjectManager
from embedding_index import EmbeddingIndex

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

def main():
    tasks = load_phased_tasks()
    ordered_tasks = sort_tasks_by_phase(tasks)

    # Try to extract project name from tasks (assume first task contains it)
    project_name = None
    if ordered_tasks:
        # Naive extraction: use the first word(s) of the first task as project name
        # (You may want to improve this logic)
        project_name = ordered_tasks[0]["task"].split()[0].lower()

    pm = ProjectManager()
    project = pm.find_project(project_name) if project_name else None

    context_snippets = []
    if project:
        # Existing project: use embedding index to get relevant code
        folder = project["folder"]
        idx = EmbeddingIndex(folder)
        # Use the concatenated tasks as the query
        query_text = "\n".join([t["task"] for t in ordered_tasks])
        context_snippets = idx.query(query_text, top_k=5)
        print(f"[Kettle] Project match found: {project['project_name']} (folder: {folder})")
    else:
        print("[Kettle] No existing project match found. Creating a new project.")

    prompt = execute_tasks_prompt(ordered_tasks, context_snippets=context_snippets, project_folder=folder if project else None)
    script = clean_code_blocks(call_perplexity(prompt))

    with open("script.py", "w") as f:
        f.write(script)
    print("✅ Generated script written to script.py")

    validate_script(script)
    execute_script(script)


if __name__ == "__main__":
    main()
