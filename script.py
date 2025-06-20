import os
import subprocess
import sys

def main():
    project_name = "tic_tac_toe"
    base_dir = os.path.expanduser("~/Desktop/Work")
    project_dir = os.path.join(base_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)

    # Set up virtual environment
    venv_dir = os.path.join(project_dir, "venv")
    if not os.path.isdir(venv_dir):
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Add logs.txt file if it doesn't exist
    logs_path = os.path.join(project_dir, "logs.txt")
    if not os.path.exists(logs_path):
        with open(logs_path, "w", encoding="utf-8") as f:
            f.write("Tic Tac Toe Game Results Log\n")

if __name__ == "__main__":
    main()