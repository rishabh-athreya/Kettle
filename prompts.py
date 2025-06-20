# prompts.py

def extract_tasks_prompt(messages):
    joined = "\n".join(f"- {msg}" for msg in messages)
    return f"""
You will receive several Slack messages that describe requirements or requests for a *single software project*. These may come from different collaborators.

Your job is to:
1. Extract all **actionable coding tasks**
2. Categorize each task into one of the following project phases:
   - "project_setup" → creating folders, repos, or initializing environments
   - "dependency_installation" → installing libraries or tools
   - "feature_implementation" → coding functionality like routes, classes, logic, etc.

Return your output as a JSON list of objects. Each object must include:
- "task": a short description of what should be done
- "source": the Slack message it came from
- "phase": one of "project_setup", "dependency_installation", or "feature_implementation"

If a message contains multiple tasks, split them into separate entries.

Messages:
{joined}
"""

def execute_tasks_prompt(sorted_tasks, codebase=None):
    task_list = "\n".join(
        f"- ({t['phase']}) {t['task']}" for t in sorted_tasks
    )
    codebase_section = ""
    if codebase:
        codebase_section = "\n\n# Existing project files (edit as needed):\n"
        for path, content in codebase.items():
            codebase_section += f"\n--- FILE: {path} ---\n{content}\n"
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
VERY IMPORTANT - IF YOU ARE MODIFYING AN EXISTING PROJECT, YOU SHOULD MODIFY EXISTING FILES IN ADDITION TO WRITING NEW ONES IN ORDER TO IMPLEMENT THE DESIRED FEATURE.
For example, if a Flask app already has a app.py file, you should update it instead of creating a new app.py.
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

Before you send the code, compile it once yourself to make sure there are no compile-time errors. This step is critical. Do not miss it.
I will be demoing this product, and I cannot risk a syntax error.

Here are the tasks to perform:
{task_list}
{codebase_section}
""" 