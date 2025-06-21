import os
import json
from keys import ANTHROPIC_API_KEY
import tempfile
import subprocess
import requests
from prompts import execute_tasks_prompt
import project_matcher

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def load_phased_tasks(filepath="json/phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t["phase"]))

def load_codebase(project_folder):
    """Load existing codebase from a project folder for LLM input"""
    codebase = {}
    
    if not os.path.exists(project_folder):
        return codebase
    
    # Common file extensions to include
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.json', '.yaml', '.yml', '.md', '.txt'}
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.env', 'dist', 'build', '.pytest_cache'}
    
    # Files to prioritize (include these first)
    priority_files = {'app.py', 'main.py', 'game.py', 'requirements.txt', 'package.json', 'Dockerfile', 'docker-compose.yml'}
    
    total_size = 0
    max_total_size = 50000  # 50KB limit to prevent API token issues
    
    for root, dirs, files in os.walk(project_folder):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        # Sort files to prioritize important ones
        files = sorted(files, key=lambda f: (f not in priority_files, f))
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_folder)
            
            # Only include code files and important config files
            if any(file.endswith(ext) for ext in code_extensions) or file in priority_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip if adding this file would exceed size limit
                    if total_size + len(content) > max_total_size:
                        print(f"⚠️  Skipping {rel_path} to stay within size limit")
                        continue
                    
                    codebase[rel_path] = content
                    total_size += len(content)
                    
                    # Stop if we've reached the size limit
                    if total_size >= max_total_size:
                        print(f"⚠️  Reached size limit ({total_size} chars), stopping codebase loading")
                        break
                        
                except Exception as e:
                    print(f"Warning: Could not read {rel_path}: {e}")
        
        # Stop walking if we've reached the size limit
        if total_size >= max_total_size:
            break
    
    print(f"📁 Loaded {len(codebase)} files ({total_size} chars) from {project_folder}")
    return codebase

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
    
    # Debug: Print prompt size
    prompt_size = len(prompt)
    print(f"📝 Prompt size: {prompt_size} characters")
    if prompt_size > 100000:  # 100KB limit
        print("⚠️  Warning: Prompt is very large, may cause API issues")
    
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e}")
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}...")  # First 500 chars
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

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

def main(existing_project_folder=None):
    tasks = load_phased_tasks()
    ordered_tasks = sort_tasks_by_phase(tasks)
    
    # If we have an existing project folder, modify the prompt to use it
    if existing_project_folder:
        print(f"🔄 Using existing project folder: {existing_project_folder}")
        codebase = load_codebase(existing_project_folder)
        prompt = execute_tasks_prompt(ordered_tasks, codebase=codebase, existing_project_folder=existing_project_folder)
        project_folder = existing_project_folder
    else:
        prompt = execute_tasks_prompt(ordered_tasks)
        project_folder = None
    
    script = clean_code_blocks(call_claude(prompt))

    with open("script.py", "w") as f:
        f.write(script)
    print("✅ Generated script written to script.py")

    validate_script(script)
    script = inject_dependencies_if_missing(script)
    execute_script(script)

    # Extract the actual project folder from the generated script
    actual_project_folder = None
    if not existing_project_folder:
        # Look for project_folder assignment in the script
        for line in script.split('\n'):
            if 'project_folder' in line and '=' in line:
                # Extract the folder name from the assignment
                if 'os.path.expanduser' in line:
                    # Handle: project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")
                    if 'project_name' in line:
                        # Look for project_name assignment
                        for name_line in script.split('\n'):
                            if 'project_name' in name_line and '=' in name_line:
                                project_name = name_line.split('=')[1].strip().strip('"\'')
                                actual_project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")
                                break
                    else:
                        # Handle: project_folder = os.path.expanduser("~/Desktop/Work/some_name")
                        folder_part = line.split('~/Desktop/Work/')[1].split('"')[0].split("'")[0]
                        actual_project_folder = os.path.expanduser(f"~/Desktop/Work/{folder_part}")
                break
    else:
        actual_project_folder = existing_project_folder

    # Save project embedding after writing files
    # Use the actual project folder that was created/modified
    if actual_project_folder:
        try:
            with open("json/messages.json", "r") as f:
                data = json.load(f)
                messages = [msg.get("text", "") for msg in data.get("messages", [])]
            project_matcher.save_project_embedding(actual_project_folder, messages)
            print(f"✅ Saved embedding for project: {actual_project_folder}")
        except Exception as e:
            print(f"[WARN] Could not save project embedding: {e}")
    else:
        print("[WARN] Could not determine actual project folder for embedding")

if __name__ == "__main__":
    main() 