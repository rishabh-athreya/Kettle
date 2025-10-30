import json
import os
import subprocess
import time
from datetime import datetime
from utils.keys import ANTHROPIC_API_KEY
import tempfile
import requests
from utils.prompts import execute_tasks_prompt, modify_existing_file_prompt
import tools.project_matcher as project_matcher

PHASE_ORDER = ["project_setup", "dependency_installation", "feature_implementation"]

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def load_phased_tasks(filepath="json/phased_tasks.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def parse_task_key(task_key):
    """Parse the task key to extract task information"""
    try:
        # Remove the outer quotes and parse the inner dict
        task_key = task_key.strip('"\'')
        # Convert string representation of dict to actual dict
        import ast
        task_dict = ast.literal_eval(task_key)
        return task_dict
    except:
        # Fallback: treat as simple string
        return {"task": task_key, "source": "unknown", "phase": "feature_implementation"}

def flatten_hierarchical_tasks(phased_tasks):
    """Convert hierarchical tasks to flat list for processing - only coding tasks"""
    flat_tasks = []
    
    # Check if this is the new structured format or old format
    if isinstance(phased_tasks, dict) and "coding" in phased_tasks:
        # New structured format: {"coding": {...}, "research": {...}, "writing": {...}}
        print("📋 Processing structured tasks (coding/research/writing)...")
        
        # Process coding tasks only
        coding_tasks = phased_tasks.get("coding", {})
        for main_task, subtasks in coding_tasks.items():
            print(f"  💻 Coding: {main_task}")
            for subtask in subtasks:
                if isinstance(subtask, dict):
                    flat_tasks.append({
                        "task": subtask.get("task", ""),
                        "source": main_task,
                        "phase": subtask.get("phase", "feature_implementation")
                    })
                    print(f"    - {subtask.get('task', '')} ({subtask.get('phase', 'feature_implementation')})")
        
        # Log research and writing tasks (but don't process them)
        research_tasks = phased_tasks.get("research", {})
        writing_tasks = phased_tasks.get("writing", {})
        
        if research_tasks:
            print(f"    🔍 Research: {len(research_tasks)} tasks (will be handled by research processor)")
        if writing_tasks:
            print(f"    ✍️  Writing: {len(writing_tasks)} tasks (will be handled separately)")
            
    elif isinstance(phased_tasks, dict):
        # Old hierarchical structure (legacy format)
        for task_key, subtasks_array in phased_tasks.items():
            task_info = parse_task_key(task_key)
            print(f"📋 Processing main task: {task_info.get('task', task_key)}")
            
            for i, subtask_group in enumerate(subtasks_array):
                print(f"  📝 Subtask group {i+1}:")
                
                # Process coding tasks only
                for coding_task in subtask_group.get("coding", []):
                    # Extract the actual task from the "Implement {...}" format
                    if coding_task.startswith("Implement "):
                        task_content = coding_task[10:]  # Remove "Implement " prefix
                        try:
                            import ast
                            task_dict = ast.literal_eval(task_content)
                            flat_tasks.append(task_dict)
                            print(f"    💻 Coding: {task_dict.get('task', task_content)}")
                        except:
                            flat_tasks.append({"task": task_content, "source": task_info.get("source", ""), "phase": task_info.get("phase", "feature_implementation")})
                            print(f"    💻 Coding: {task_content}")
                    else:
                        flat_tasks.append({"task": coding_task, "source": task_info.get("source", ""), "phase": task_info.get("phase", "feature_implementation")})
                        print(f"    💻 Coding: {coding_task}")
                
                # Skip research and writing tasks - these will be handled separately
                research_count = len(subtask_group.get("research", []))
                writing_count = len(subtask_group.get("writing", []))
                if research_count > 0:
                    print(f"    🔍 Research: {research_count} tasks (will be handled by research processor)")
                if writing_count > 0:
                    print(f"    ✍️  Writing: {writing_count} tasks (will be handled separately)")
    else:
        # Flat structure (legacy format) - filter for coding tasks only
        for task in phased_tasks:
            if task.get("category", "coding") == "coding":
                flat_tasks.append(task)
    
    return flat_tasks

def sort_tasks_by_phase(tasks):
    return sorted(tasks, key=lambda t: PHASE_ORDER.index(t.get("phase", "feature_implementation")))

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

def generate_script_for_existing_project(ordered_tasks, existing_project_folder, codebase):
    """Generate a script specifically for modifying existing projects with strict preservation rules"""
    print(f"🔧 Generating modification script for existing project: {existing_project_folder}")
    
    # Create a script that uses the specialized prompt for each file modification
    script_lines = [
        "import os",
        "import subprocess", 
        "import sys",
        "import json",
        "import requests",
        "",
        f"# Project folder: {existing_project_folder}",
        f"project_folder = '{existing_project_folder}'",
        "",
        "# API configuration",
        "ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')",
        "ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'",
        "",
        "def call_claude(prompt):",
        "    headers = {",
        "        'x-api-key': ANTHROPIC_API_KEY,",
        "        'Content-Type': 'application/json',",
        "        'anthropic-version': '2023-06-01'",
        "    }",
        "    body = {",
        "        'model': 'claude-3-5-sonnet-20241022',",
        "        'max_tokens': 8000,",
        "        'messages': [{'role': 'user', 'content': prompt}],",
        "        'temperature': 0.1  # Lower temperature for more consistent modifications",
        "    }",
        "    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
",
        "    response.raise_for_status()",
        "    return response.json()['content'][0]['text']",
        "",
        "def modify_file_with_preservation(file_path, task_description):",
        "    print(f'Modifying {file_path} with preservation rules...')",
        "    ",
        "    # Read existing file content",
        "    with open(file_path, 'r') as f:",
        "        existing_content = f.read()",
        "    ",
        "    # Create specialized prompt for file modification",
        "    prompt = f'''You are modifying an existing file: {file_path}",
        "",
        "**TASK TO IMPLEMENT:**",
        f"{''}",
        "",
        "**EXISTING FILE CONTENT:**",
        "```",
        f"{{existing_content}}",
        "```",
        "",
        "**ABSOLUTELY CRITICAL RULES:**",
        "1. **PRESERVE ALL EXISTING FUNCTIONALITY** - The file must work exactly as before",
        "2. **ADDITIVE CHANGES ONLY** - Only add new code, never modify existing code", 
        "3. **NO REFACTORING** - Do not reorganize, restructure, or improve existing code",
        "4. **NO BUG FIXES** - Do not fix existing bugs unless explicitly requested",
        "5. **NO STYLE CHANGES** - Do not change formatting, variable names, or code style",
        "6. **NO IMPORT MODIFICATIONS** - Do not change existing import statements",
        "7. **NO FUNCTION CHANGES** - Do not modify existing function signatures or logic",
        "8. **NO CLASS MODIFICATIONS** - Do not modify existing class definitions",
        "",
        "**REQUIRED APPROACH:**",
        "1. Read the existing file content (provided above)",
        "2. Add new code at the end (before any main execution block like `if __name__ == '__main__':`)",
        "3. Do not modify any existing code",
        "4. Only add new imports if absolutely necessary for the new feature",
        "5. Ensure the new feature integrates with existing functionality without breaking it",
        "",
        "**RETURN FORMAT:**",
        "Return ONLY the complete updated file content with your additions. Do not include explanations or markdown formatting.",
        "'''",
        "    ",
        "    # Get modified content from Claude",
        "    modified_content = call_claude(prompt)",
        "    ",
        "    # Clean up the response (remove markdown if present)",
        "    if '```' in modified_content:",
        "        modified_content = modified_content.split('```')[1] if len(modified_content.split('```')) > 1 else modified_content",
        "    ",
        "    # Write the modified content back to the file",
        "    with open(file_path, 'w') as f:",
        "        f.write(modified_content)",
        "    ",
        "    print(f'✅ Successfully modified {file_path}')",
        "",
        "# Tasks to implement:",
    ]
    
    # Add task descriptions
    for i, task in enumerate(ordered_tasks, 1):
        script_lines.append(f"# {i}. {task['task']} (phase: {task['phase']})")
    
    script_lines.extend([
        "",
        "# Main execution",
        "print('🔧 Starting modifications with strict preservation rules...')",
        "",
        "# Determine which files to modify based on tasks",
        "files_to_modify = []",
    ])
    
    # Add logic to determine which files to modify
    for task in ordered_tasks:
        task_desc = task['task']
        script_lines.extend([
            f"# Task: {task_desc}",
            f"if any(keyword in '{task_desc}'.lower() for keyword in ['game', 'pygame', 'flappy']):",
            "    files_to_modify.append(('game.py', f'Add feature: {task_desc}'))",
            "elif any(keyword in '{task_desc}'.lower() for keyword in ['web', 'flask', 'app', 'server']):",
            "    files_to_modify.append(('app.py', f'Add feature: {task_desc}'))",
            "else:",
            "    files_to_modify.append(('main.py', f'Add feature: {task_desc}'))",
        ])
    
    script_lines.extend([
        "",
        "# Apply modifications",
        "for file_path, task_description in files_to_modify:",
        "    full_path = os.path.join(project_folder, file_path)",
        "    if os.path.exists(full_path):",
        "        modify_file_with_preservation(full_path, task_description)",
        "    else:",
        "        print(f'⚠️  File {full_path} does not exist, skipping')",
        "",
        "print('✅ All modifications completed with preservation rules')",
    ])
    
    return '\n'.join(script_lines)

def main(existing_project_folder=None):
    phased_tasks = load_phased_tasks()
    
    # Convert hierarchical structure to flat list (coding tasks only)
    print("🔄 Processing hierarchical tasks...")
    flat_tasks = flatten_hierarchical_tasks(phased_tasks)
    
    if not flat_tasks:
        print("❌ No coding tasks found to execute")
        return
    
    print(f"✅ Flattened {len(flat_tasks)} coding tasks from hierarchical structure")
    
    # Sort tasks by phase
    ordered_tasks = sort_tasks_by_phase(flat_tasks)

    # If no explicit folder was provided, try to select the closest existing project by embeddings
    if existing_project_folder is None:
        try:
            query_messages = [t.get('task', '') for t in ordered_tasks if t.get('task')]
            closest_project, similarity = project_matcher.find_closest_project(query_messages)
            if closest_project:
                print(f"🔎 Found closest existing project: {closest_project} (sim={similarity:.2f})")
                existing_project_folder = closest_project
            else:
                print("🔎 No sufficiently similar existing project found; creating a new one")
        except Exception as e:
            print(f"[WARN] Embedding-based project selection failed: {e}")
    
    # If we have an existing project folder, use specialized modification approach
    if existing_project_folder:
        print(f"🔄 Using existing project folder: {existing_project_folder}")
        codebase = load_codebase(existing_project_folder)
        
        # Use specialized script for existing projects
        script = generate_script_for_existing_project(ordered_tasks, existing_project_folder, codebase)
    else:
        # Use regular prompt for new projects
        prompt = execute_tasks_prompt(ordered_tasks)
        script = clean_code_blocks(call_claude(prompt))

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
                                project_name = name_line.split('=')[1].strip().strip("\"'")
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
