import os
import subprocess
import sys

# Project setup
project_name = "flappy_bird"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory if it doesn't exist
os.makedirs(project_folder, exist_ok=True)

# Create logs.txt file
logs_path = os.path.join(project_folder, "logs.txt")
if not os.path.exists(logs_path):
    with open(logs_path, "w") as f:
        f.write("Flappy Bird Score Log\n")
    print(f"Created logs.txt at: {logs_path}")

# Modify game.py to add logging functionality
game_path = os.path.join(project_folder, "game.py")
with open(game_path, "r") as f:
    game_code = f.read()

# Add logging imports at the top of the file
if "import datetime" not in game_code:
    game_code = "import datetime\n" + game_code

# Modify the Game class to add logging functionality
game_code = game_code.replace(
    "    pygame.quit()",
    """    # Log the score
    with open('logs.txt', 'a') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp} - Score: {game.score}\\n")
    pygame.quit()"""
)

# Write the modified game.py
with open(game_path, "w") as f:
    f.write(game_code)
print(f"Updated game.py with logging functionality at: {game_path}")

# Verify files exist
if not os.path.exists(logs_path):
    print("Error: logs.txt was not created!")
    sys.exit(1)
if not os.path.exists(game_path):
    print("Error: game.py was not updated!")
    sys.exit(1)