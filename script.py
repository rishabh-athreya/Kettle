import os
import subprocess
import sys

# Project setup
project_name = "flappy_bird"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory
os.makedirs(project_folder, exist_ok=True)

# Create virtual environment
venv_path = os.path.join(project_folder, "venv")
if not os.path.exists(venv_path):
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

# Install pygame using venv pip
if os.name == 'nt':  # Windows
    pip_path = os.path.join(venv_path, "Scripts", "pip")
else:  # Unix/Linux/Mac
    pip_path = os.path.join(venv_path, "bin", "pip")
try:
    subprocess.run([pip_path, "install", "pygame"], check=True)
except subprocess.CalledProcessError as e:
    print("pip install failed, retrying with --break-system-packages due to PEP 668...")
    subprocess.run([pip_path, "install", "--break-system-packages", "pygame"], check=True)

# Create game file
game_code = '''
import pygame
import random

# Initialize Pygame
pygame.init()

# Game window settings
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Bird settings
BIRD_WIDTH = 40
BIRD_HEIGHT = 30
bird_x = WINDOW_WIDTH // 3
bird_y = WINDOW_HEIGHT // 2
bird_velocity = 0
GRAVITY = 0.5
JUMP_STRENGTH = -8

# Pipe settings
PIPE_WIDTH = 60
PIPE_GAP = 150
pipe_x = WINDOW_WIDTH
pipe_height = random.randint(100, WINDOW_HEIGHT - PIPE_GAP - 100)

def draw_bird(x, y):
    pygame.draw.rect(WINDOW, BLACK, (x, y, BIRD_WIDTH, BIRD_HEIGHT))

def draw_pipes(x, height):
    # Bottom pipe
    pygame.draw.rect(WINDOW, GREEN, (x, height + PIPE_GAP, PIPE_WIDTH, WINDOW_HEIGHT))
    # Top pipe
    pygame.draw.rect(WINDOW, GREEN, (x, 0, PIPE_WIDTH, height))

def check_collision(bird_rect, top_pipe, bottom_pipe):
    return bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe)

def game_loop():
    global bird_y, bird_velocity, pipe_x, pipe_height
    
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = JUMP_STRENGTH

        # Bird physics
        bird_velocity += GRAVITY
        bird_y += bird_velocity

        # Move pipe
        pipe_x -= 3
        if pipe_x < -PIPE_WIDTH:
            pipe_x = WINDOW_WIDTH
            pipe_height = random.randint(100, WINDOW_HEIGHT - PIPE_GAP - 100)

        # Draw everything
        WINDOW.fill(WHITE)
        draw_bird(bird_x, bird_y)
        draw_pipes(pipe_x, pipe_height)

        # Collision detection
        bird_rect = pygame.Rect(bird_x, bird_y, BIRD_WIDTH, BIRD_HEIGHT)
        top_pipe = pygame.Rect(pipe_x, 0, PIPE_WIDTH, pipe_height)
        bottom_pipe = pygame.Rect(pipe_x, pipe_height + PIPE_GAP, PIPE_WIDTH, WINDOW_HEIGHT)

        if check_collision(bird_rect, top_pipe, bottom_pipe):
            running = False

        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    game_loop()
'''

# Write game.py to project directory
game_path = os.path.join(project_folder, "game.py")
with open(game_path, "w") as f:
    f.write(game_code)
print(f"Wrote game.py to: {game_path}")
if not os.path.exists(game_path):
    print("Error: game.py was not created!")
    sys.exit(1)