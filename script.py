import os
import subprocess
import sys

# Project setup
project_name = "basic_python_project"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory
os.makedirs(project_folder, exist_ok=True)

# Create virtual environment
venv_path = os.path.join(project_folder, "venv")
if not os.path.exists(venv_path):
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

# Install dependencies using venv pip
if os.name == 'nt':  # Windows
    pip_path = os.path.join(venv_path, "Scripts", "pip")
else:  # Unix/Linux/Mac
    pip_path = os.path.join(venv_path, "bin", "pip")

try:
    subprocess.run([pip_path, "install", "requests"], check=True)
except subprocess.CalledProcessError as e:
    print("pip install failed, retrying with --break-system-packages due to PEP 668...")
    subprocess.run([pip_path, "install", "--break-system-packages", "requests"], check=True)

# Create main application file
app_code = '''
import requests

def main():
    print("Basic Python Project")
    try:
        response = requests.get("https://api.github.com")
        if response.status_code == 200:
            print("Successfully connected to GitHub API")
        else:
            print(f"Failed to connect. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
'''

# Write app.py to project directory
app_path = os.path.join(project_folder, "app.py")
with open(app_path, "w") as f:
    f.write(app_code)
print(f"Wrote app.py to: {app_path}")
if not os.path.exists(app_path):
    print("Error: app.py was not created!")
    sys.exit(1)

# Create requirements.txt
requirements_code = '''
requests>=2.28.0
'''

requirements_path = os.path.join(project_folder, "requirements.txt")
with open(requirements_path, "w") as f:
    f.write(requirements_code)
print(f"Wrote requirements.txt to: {requirements_path}")
if not os.path.exists(requirements_path):
    print("Error: requirements.txt was not created!")
    sys.exit(1)

# Create README.md
readme_code = '''
# Basic Python Project

A simple Python project template with virtual environment setup.

## Setup

1. Create virtual environment: