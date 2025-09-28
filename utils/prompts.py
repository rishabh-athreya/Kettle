# prompts.py

def extract_tasks_prompt(messages):
    joined = "\n".join(f"- {msg}" for msg in messages)
    
    # Check if this is a modification request
    is_modification = any(keyword in joined.lower() for keyword in [
        "modify", "update", "change", "add to", "enhance", "improve", 
        "fix", "adjust", "tweak", "refactor", "extend", "expand"
    ])
    
    modification_context = ""
    if is_modification:
        modification_context = """
**MODIFICATION CONTEXT:**
- These tasks are for modifying an existing project
- Focus on feature_implementation phase tasks
- Tasks should be additive changes to existing code
- Avoid project_setup tasks unless explicitly requested
- Prioritize specific feature additions and improvements
"""
    
    return f"""Extract actionable coding tasks from these Slack messages and categorize them:

**Phases:**
- project_setup: folders, repos, environments (only for new projects)
- dependency_installation: libraries, tools, packages  
- feature_implementation: code, routes, logic, features

{modification_context}

**Rules:**
- Infer dependencies (e.g., web app → Flask, game → pygame)
- Split multi-task messages into separate entries
- Return JSON list with: task, source, phase
- For modifications: focus on specific feature changes
- For new projects: include setup and dependency tasks

Messages:
{joined}"""

def modify_existing_file_prompt(task_description, existing_file_content, file_path):
    """Specialized prompt for modifying existing files with strict preservation rules"""
    return f"""You are modifying an existing file: {file_path}

**TASK TO IMPLEMENT:**
{task_description}

**EXISTING FILE CONTENT:**
```
{existing_file_content}
```

**ABSOLUTELY CRITICAL RULES:**
1. **PRESERVE ALL EXISTING FUNCTIONALITY** - The file must work exactly as before
2. **ADDITIVE CHANGES ONLY** - Only add new code, never modify existing code
3. **NO REFACTORING** - Do not reorganize, restructure, or improve existing code
4. **NO BUG FIXES** - Do not fix existing bugs unless explicitly requested
5. **NO STYLE CHANGES** - Do not change formatting, variable names, or code style
6. **NO IMPORT MODIFICATIONS** - Do not change existing import statements
7. **NO FUNCTION CHANGES** - Do not modify existing function signatures or logic
8. **NO CLASS MODIFICATIONS** - Do not modify existing class definitions

**REQUIRED APPROACH:**
1. Read the existing file content (provided above)
2. Add new code at the end (before any main execution block like `if __name__ == '__main__':`)
3. Do not modify any existing code
4. Only add new imports if absolutely necessary for the new feature
5. Ensure the new feature integrates with existing functionality without breaking it

**EXAMPLE PATTERN:**
```python
# [Keep all existing code exactly as is]

# NEW FEATURE: [feature name]
def new_feature_function():
    # New functionality here
    pass

# [Keep existing main execution block exactly as is]
```

**RETURN FORMAT:**
Return ONLY the complete updated file content with your additions. Do not include explanations or markdown formatting.

**VERIFICATION:**
Before returning, verify that:
- All existing code is preserved exactly
- New functionality is added without breaking existing functionality
- The file will still run and work as before
- New features are properly integrated"""

def execute_tasks_prompt(sorted_tasks, codebase=None, existing_project_folder=None):
    # Separate selected and rejected tasks
    selected_tasks = [t for t in sorted_tasks if t.get('selectionStatus') == 'selected']
    rejected_tasks = [t for t in sorted_tasks if t.get('selectionStatus') == 'rejected']
    
    task_list = "\n".join(f"- ({t['phase']}) {t['task']}" for t in selected_tasks)
    
    # Add rejected tasks as comments
    rejected_section = ""
    if rejected_tasks:
        rejected_list = "\n".join(f"# REJECTED: {t['task']}" for t in rejected_tasks)
        rejected_section = f"""

**REJECTED TASKS (DO NOT IMPLEMENT THESE):**
{rejected_list}

**CRITICAL: DO NOT IMPLEMENT REJECTED FEATURES**
- The above rejected tasks must NOT be implemented
- Do not add any code related to these rejected features
- Even if a rejected feature seems "logical" or "necessary", do not include it
- If a selected task depends on a rejected task, implement only the parts that don't require the rejected feature
- If you cannot implement a selected task without a rejected dependency, skip that task and add a comment explaining why
"""
    
    codebase_section = ""
    if codebase:
        codebase_section = "\n\nEXISTING FILES AND CONTENTS (DO NOT REMOVE ANY OF THIS LOGIC):\n"
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
    
    return f"""Write a Python script that executes these SELECTED tasks in order:

{task_list}

{existing_project_section}

**CRITICAL FEATURE CONSTRAINT:**
- ONLY implement the features explicitly listed in the selected tasks above
- Do NOT add any features that are not explicitly mentioned in the selected tasks
- Do NOT add "logical" or "necessary" features that weren't explicitly selected
- If a feature seems like it should be included but wasn't selected, do NOT include it

{rejected_section}

**ABSOLUTELY CRITICAL CODE PRESERVATION REQUIREMENTS:**
- **NEVER MODIFY EXISTING FUNCTIONALITY** - Only ADD new features
- **PRESERVE ALL EXISTING CODE** - Do not change, remove, or rewrite any existing code
- **ADDITIVE CHANGES ONLY** - Only add new functions, classes, or code blocks
- **NO REFACTORING** - Do not reorganize, restructure, or improve existing code
- **NO BUG FIXES** - Do not fix existing bugs unless explicitly requested
- **NO OPTIMIZATIONS** - Do not optimize existing code unless explicitly requested
- **NO STYLE CHANGES** - Do not change formatting, variable names, or code style
- **NO IMPORT CHANGES** - Do not modify existing import statements
- **NO FUNCTION SIGNATURE CHANGES** - Do not change existing function parameters or return types
- **NO CLASS MODIFICATIONS** - Do not modify existing class definitions, methods, or attributes

**SPECIFIC PRESERVATION RULES:**
- If adding logging: Create a separate logging function, do not modify existing functions
- If adding debugging: Add debug prints as separate lines, do not modify existing logic
- If adding features: Create new functions/classes, do not modify existing ones
- If adding configuration: Create new config files, do not modify existing ones
- If adding tests: Create new test files, do not modify existing code
- If adding documentation: Create new doc files, do not modify existing code comments

**EXISTING CODE PROTECTION:**
- When modifying files with existing code, use this pattern:
  1. Read the existing file content
  2. Add new code at the end (before the main execution block)
  3. Do not modify any existing code
  4. Only add new imports if absolutely necessary
- Example for adding features to existing game:
  ```python
  # Read existing game code
  with open(game_file, 'r') as f:
      existing_code = f.read()
  
  # Add new feature code at the end (before main execution)
  new_feature_code = '''
  # NEW FEATURE: [feature name]
  def new_feature_function():
      # New functionality here
      pass
  
  # Add feature to existing game loop (if needed)
  # Do NOT modify existing game loop, only add calls to new functions
  '''
  
  # Combine existing code with new feature
  updated_code = existing_code + new_feature_code
  
  # Write back to file
  with open(game_file, 'w') as f:
      f.write(updated_code)
  ```

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

**CRITICAL IMPORT REQUIREMENTS:**
- The script MUST start with these imports at the very top, in this order:
    import os
    import subprocess
    import sys
- Do NOT omit any of these imports, even if you think they are not needed.

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

def fetch_messages():
    with open("json/messages.json", "r") as f:
        data = json.load(f)
        messages = data.get("messages", [])
        # Extract just the text content from each message
        return [msg.get("text", "") for msg in messages if msg.get("text", "").strip()] 