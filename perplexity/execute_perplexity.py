import os
import json
from keys import PERPLEXITY_API_KEY
import tempfile
import subprocess
import requests
from prompts_perplexity import execute_tasks_prompt
from project_matcher_perplexity import find_closest_project, save_project_embedding
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
    
    # Debug: Show the first 20 lines of the temp file
    print("\n🔍 DEBUG: First 20 lines of temp file:")
    with open(temp_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {repr(line)}")
    
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
    
    # Check for virtual environment creation
    if "venv" not in script_code.lower() and "virtualenv" not in script_code.lower():
        print("⚠️  Warning: Script may not create virtual environment")
    
    # Check for pip install commands
    if "pip install" not in script_code.lower() and "subprocess.run" not in script_code.lower():
        print("⚠️  Warning: Script may not install dependencies")
    
    # Check for common dependency patterns that should trigger installation
    common_deps = ["flask", "pygame", "requests", "numpy", "pandas", "django", "fastapi"]
    found_deps = [dep for dep in common_deps if dep in script_code.lower()]
    if found_deps:
        print(f"🔍 Found potential dependencies: {found_deps}")
        if "pip install" not in script_code.lower():
            print("⚠️  Warning: Dependencies detected but no pip install found")
    
    # Check for syntax errors
    try:
        compile(script_code, '<string>', 'exec')
        print("✅ Script syntax is valid")
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR in generated script:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        print("\n🔧 Attempting to fix indentation...")
        
        # Try to fix the script
        fixed_script = fix_indentation(script_code)
        try:
            compile(fixed_script, '<string>', 'exec')
            print("✅ Fixed script syntax is valid")
            return fixed_script
        except SyntaxError as e2:
            print(f"❌ Still has syntax error after fixing:")
            print(f"   Line {e2.lineno}: {e2.text}")
            print(f"   Error: {e2.msg}")
            raise ValueError(f"Generated script has unfixable syntax error: {e2}")
    
    return script_code

def fix_indentation(script_code):
    """Fix common indentation issues in generated scripts"""
    lines = script_code.split('\n')
    fixed_lines = []
    indent_level = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append('')
            continue
        
        # Remove any tabs and replace with 4 spaces
        line = line.replace('\t', '    ')
        
        # Lines that should be at base level (no indentation)
        base_level_keywords = [
            'import ', 'from ', 'def ', 'class ', 'if __name__', 
            'PHASE_ORDER', 'project_name', 'project_folder', 'GEMINI_API_URL',
            '# Project setup', '# Create project directory', '# Create virtual environment',
            '# Install dependencies', '# Your task implementation'
        ]
        
        # Lines that should be indented one level
        indent_one_keywords = [
            'print(', 'subprocess.run(', 'os.makedirs(', 'os.path.exists(', 
            'with open(', 'if not ', 'else:', 'elif ', 'try:', 'except ',
            'finally:', 'for ', 'while ', 'return ', 'break', 'continue'
        ]
        
        # Check if this line should be at base level
        should_be_base = any(stripped.startswith(keyword) for keyword in base_level_keywords)
        
        # Check if this line should be indented one level
        should_be_indented = any(stripped.startswith(keyword) for keyword in indent_one_keywords)
        
        # Handle indentation
        if should_be_base:
            indent_level = 0
            fixed_lines.append(stripped)
        elif should_be_indented:
            # Ensure it's indented exactly one level
            fixed_lines.append('    ' + stripped)
        elif stripped.endswith(':'):
            # This is likely a control structure that opens a block
            if not line.startswith('    '):
                fixed_lines.append('    ' + stripped)
            else:
                fixed_lines.append(line)
            indent_level += 1
        else:
            # For other lines, maintain current indentation level
            if indent_level > 0 and not line.startswith('    '):
                fixed_lines.append('    ' * indent_level + stripped)
            else:
                fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def inject_dependencies_if_missing(script_code):
    """Inject dependency installation if missing from the script"""
    common_deps = {
        "flask": "flask",
        "pygame": "pygame", 
        "requests": "requests",
        "numpy": "numpy",
        "pandas": "pandas",
        "django": "django",
        "fastapi": "fastapi",
        "sqlalchemy": "sqlalchemy",
        "jinja2": "jinja2",
        "werkzeug": "werkzeug"
    }
    
    # Find dependencies used in the script
    used_deps = []
    for dep_name, pip_name in common_deps.items():
        if dep_name in script_code.lower():
            used_deps.append(pip_name)
    
    if not used_deps:
        return script_code
    
    # Check if pip install is already present
    if "pip install" in script_code.lower():
        return script_code
    
    # Inject dependency installation after venv creation
    lines = script_code.split('\n')
    new_lines = []
    venv_created = False
    
    for line in lines:
        new_lines.append(line)
        
        # After venv creation, inject pip install
        if ("venv" in line.lower() or "virtualenv" in line.lower()) and not venv_created:
            venv_created = True
            new_lines.append("")
            new_lines.append("# Install dependencies")
            for dep in used_deps:
                new_lines.append(f'subprocess.run([sys.executable, "-m", "pip", "install", "{dep}"], check=True)')
            new_lines.append("")
    
    return '\n'.join(new_lines)

def gather_code_files(project_folder):
    print(f"[DEBUG] Gathering files from: {project_folder}")
    
    # Check if project folder exists
    if not os.path.exists(os.path.expanduser(project_folder)):
        print(f"[DEBUG] Project folder {project_folder} does not exist yet")
        return {}
    
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
    
    # Check if the work directory exists
    if not os.path.exists(work_dir):
        print(f"[DEBUG] Work directory {work_dir} does not exist yet")
        return None
    
    try:
    folders = [os.path.join(work_dir, d) for d in os.listdir(work_dir) if os.path.isdir(os.path.join(work_dir, d))]
    if not folders:
        return None
    latest_folder = max(folders, key=os.path.getmtime)
    return latest_folder
    except (OSError, FileNotFoundError) as e:
        print(f"[DEBUG] Error accessing work directory: {e}")
        return None

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

    script = validate_script(script)
    script = inject_dependencies_if_missing(script)
    script = fix_indentation(script)
    execute_script(script)

    # After script runs, get the actual folder created/modified
    if creating_new_project:
        actual_folder = get_latest_project_folder()
        print(f"[DEBUG] Detected actual project folder: {actual_folder}")
        if actual_folder:
            save_project_embedding(actual_folder, messages)

if __name__ == "__main__":
    main()
