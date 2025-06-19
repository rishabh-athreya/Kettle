import json
import os
import tempfile
import subprocess
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

# Load task list from JSON
def load_phased_tasks(filepath="phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

# Sort tasks by project phase
def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t["phase"]))

# Generate Claude prompt to synthesize Python script
def build_prompt(sorted_tasks):
    task_list = "\n".join(
        f"- ({t['phase']}) {t['task']}" for t in sorted_tasks
    )
    return f"""
{HUMAN_PROMPT} You are a coding assistant. Write a single Python script that performs the following project tasks **in the correct order**. 

There are three types of tasks:
1. "project_setup" – create folders, files, initialize structure
2. "dependency_installation" – install Python packages via pip
3. "feature_implementation" – write code into files (e.g. Flask routes)

Here are the tasks to implement:

{task_list}

Requirements:
- All tasks must be performed in order.
- Install any packages into a virtual environment inside the project folder.
- Create or update source files as needed.
- Only return valid Python code. Do not include explanations or comments.

{AI_PROMPT}
""".strip()

# Call Claude to generate the script
def call_claude(prompt):
    client = Anthropic()
    response = client.completions.create(
        model="claude-2.1",
        prompt=prompt,
        stop_sequences=[HUMAN_PROMPT],
        max_tokens_to_sample=1000,
        temperature=0.3,
    )
    return response.completion.strip()

# Save to temp file and execute
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

# Main driver
def main():
    tasks = load_phased_tasks()
    ordered_tasks = sort_tasks_by_phase(tasks)
    prompt = build_prompt(ordered_tasks)
    script = call_claude(prompt)
    execute_script(script)

if __name__ == "__main__":
    main()
