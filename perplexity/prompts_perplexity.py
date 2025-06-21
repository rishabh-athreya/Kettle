# prompts.py

def extract_tasks_prompt(messages):
    joined = "\n".join(f"- {msg}" for msg in messages)
    return f"""Extract actionable coding tasks from these Slack messages and categorize them:

**Phases:**
- project_setup: folders, repos, environments
- dependency_installation: libraries, tools, packages  
- feature_implementation: code, routes, logic

**Rules:**
- Infer dependencies (e.g., web app → Flask, game → pygame)
- Split multi-task messages into separate entries
- Return JSON list with: task, source, phase

Messages:
{joined}"""

def execute_tasks_prompt(sorted_tasks, codebase=None, existing_project_folder=None):
    task_list = "\n".join(f"- ({t['phase']}) {t['task']}" for t in sorted_tasks)
    
    codebase_section = ""
    if codebase:
        codebase_section = "\n\nExisting files:\n"
        for path, content in codebase.items():
            codebase_section += f"\n--- {path} ---\n{content}\n"
    
    # Add existing project folder info if provided
    existing_project_section = ""
    if existing_project_folder:
        existing_project_section = f"""
**EXISTING PROJECT FOLDER:**
- Use the existing project folder: {existing_project_folder}
- Do NOT create a new project folder
- Modify existing files in this folder instead of creating new ones
- If the folder doesn't exist, create it
"""
    
    return f"""Write a Python script that executes these tasks in order:

{task_list}

{existing_project_section}

**CRITICAL CODE PRESERVATION REQUIREMENTS:**
- When modifying existing files, PRESERVE ALL EXISTING FUNCTIONALITY
- Only ADD new logic, features, or code - do NOT remove existing code unless the task explicitly says to do so
- If adding logging, debugging, or monitoring features, add them alongside existing code, not as replacements
- If the task asks to "add" something, only add it - do not rewrite or replace existing functionality
- If the task asks to "modify" something, make minimal changes that preserve the original behavior
- Only remove or replace code if the task explicitly says "remove", "replace", "delete", or "rewrite"
- When in doubt, ADD rather than REPLACE

**CRITICAL FILE CREATION REQUIREMENTS:**
- ALWAYS write application code to files in the project directory
- Create app.py (or main.py) for web applications
- Create game.py for games or standalone applications
- Use proper file paths: os.path.join(project_folder, "app.py")
- Write files BEFORE trying to run them
- Example: with open(os.path.join(project_folder, "app.py"), "w") as f: f.write(app_code)
- After writing each file, print its path for debugging
- After writing files, check that they exist; if not, print an error and exit

**CRITICAL EXECUTION REQUIREMENT:**
- Do NOT run or execute any of the files after writing them. Only write the files to disk.

**CRITICAL INDENTATION REQUIREMENTS:**
- Use EXACTLY 4 spaces for each indentation level
- NEVER use tabs
- Import statements must have ZERO indentation (start at column 1)
- All other code must be properly indented with 4 spaces per level
- Check that your indentation is consistent throughout

**CRITICAL SYNTAX REQUIREMENTS:**
- All code must be valid Python syntax
- No syntax errors or indentation errors
- Return ONLY the Python code, no explanations or markdown

**CRITICAL VIRTUAL ENVIRONMENT REQUIREMENTS:**
- ALWAYS use the virtual environment's pip for installing dependencies
- NEVER use sys.executable for pip install commands
- Use the correct pip path: venv_path + "/bin/pip" (Unix/Mac) or venv_path + "/Scripts/pip" (Windows)
- Example: subprocess.run([os.path.join(venv_path, "bin", "pip"), "install", "flask"], check=True)
- If you encounter a pip error about "externally-managed-environment" or PEP 668, add the '--break-system-packages' flag to the pip install command.
- Example: subprocess.run([pip_path, "install", "--break-system-packages", "flask"], check=True)

**CRITICAL ERROR HANDLING REQUIREMENTS:**
- If a subprocess call fails, print the error and exit.
- If pip install fails due to PEP 668, retry with '--break-system-packages'.
- If dependencies are not installed, print a warning and suggest a manual pip install command.

**Template structure (copy this exact indentation):**
```python
import os
import subprocess
import sys

# Project setup
project_name = "..."
project_folder = os.path.expanduser(f"~/Desktop/Work/{{project_name}}")

# Create project directory
os.makedirs(project_folder, exist_ok=True)

# Create virtual environment
venv_path = os.path.join(project_folder, "venv")
if not os.path.exists(venv_path):
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

# Install dependencies using venv pip (NOT sys.executable)
if os.name == 'nt':  # Windows
    pip_path = os.path.join(venv_path, "Scripts", "pip")
else:  # Unix/Linux/Mac
    pip_path = os.path.join(venv_path, "bin", "pip")
try:
    subprocess.run([pip_path, "install", "flask"], check=True)
except subprocess.CalledProcessError as e:
    print("pip install failed, retrying with --break-system-packages due to PEP 668...")
    subprocess.run([pip_path, "install", "--break-system-packages", "flask"], check=True)

# Create application file
app_code = '''
# Your application code here
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    app.run(debug=True)
'''

# Write app.py to project directory
app_path = os.path.join(project_folder, "app.py")
with open(app_path, "w") as f:
    f.write(app_code)
print(f"Wrote app.py to: {{app_path}}")
if not os.path.exists(app_path):
    print("Error: app.py was not created!")
    sys.exit(1)

# Do NOT run or execute app.py or any other files. Only write them to disk.
```

{codebase_section}""" 