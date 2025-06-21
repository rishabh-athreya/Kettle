import os
import subprocess
import sys

# Project setup
project_name = "flappy_bird"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory if it doesn't exist
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
    print("pip install failed, retrying with --break-system-packages...")
    subprocess.run([pip_path, "install", "--break-system-packages", "pygame"], check=True)

# Create logs.txt file
logs_path = os.path.join(project_folder, "logs.txt")
with open(logs_path, "w") as f:
    f.write("Game Results Log\n")
print(f"Created logs file at: {logs_path}")

# Update game.py with logging and bird sprite
game_code = '''
import pygame
import random
import sys
import datetime

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRAVITY = 0.25
FLAP_STRENGTH = -7
PIPE_SPEED = 3
PIPE_GAP = 150
PIPE_FREQUENCY = 1500  # milliseconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

# Create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

class Bird:
    def __init__(self):
        self.x = SCREEN_WIDTH // 3
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.rect = pygame.Rect(self.x, self.y, 30, 30)
        # Load bird sprite
        try:
            self.sprite = pygame.image.load("bird.png")
            self.sprite = pygame.transform.scale(self.sprite, (30, 30))
        except:
            self.sprite = None
    
    def flap(self):
        self.velocity = FLAP_STRENGTH
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = self.y
    
    def draw(self):
        if self.sprite:
            screen.blit(self.sprite, self.rect)
        else:
            pygame.draw.rect(screen, WHITE, self.rect)

class Pipe:
    def __init__(self):
        self.gap_y = random.randint(100, SCREEN_HEIGHT - 100)
        self.x = SCREEN_WIDTH
        self.top_height = self.gap_y - PIPE_GAP // 2
        self.bottom_height = SCREEN_HEIGHT - (self.gap_y + PIPE_GAP // 2)
        self.top_rect = pygame.Rect(self.x, 0, 50, self.top_height)
        self.bottom_rect = pygame.Rect(self.x, SCREEN_HEIGHT - self.bottom_height, 50, self.bottom_height)
        self.passed = False
    
    def update(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
    
    def draw(self):
        pygame.draw.rect(screen, GREEN, self.top_rect)
        pygame.draw.rect(screen, GREEN, self.bottom_rect)

class Game:
    def __init__(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        self.last_pipe = pygame.time.get_ticks()
        self.start_time = datetime.datetime.now()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.log_game()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.bird.flap()
    
    def update(self):
        self.bird.update()
        
        now = pygame.time.get_ticks()
        if now - self.last_pipe > PIPE_FREQUENCY:
            self.pipes.append(Pipe())
            self.last_pipe = now
        
        for pipe in self.pipes[:]:
            pipe.update()
            
            if pipe.x < -50:
                self.pipes.remove(pipe)
            
            if not pipe.passed and pipe.x < self.bird.x:
                self.score += 1
                pipe.passed = True
            
            if (pipe.top_rect.colliderect(self.bird.rect) or 
                pipe.bottom_rect.colliderect(self.bird.rect) or
                self.bird.y < 0 or self.bird.y > SCREEN_HEIGHT):
                self.log_game()
                self.reset()
    
    def log_game(self):
        duration = datetime.datetime.now() - self.start_time
        with open("logs.txt", "a") as f:
            f.write(f"Game ended at {datetime.datetime.now()}, Score: {self.score}, Duration: {duration}\\n")
    
    def reset(self):
        self.bird = Bird()
        self.pipes.clear()
        self.score = 0
        self.last_pipe = pygame.time.get_ticks()
        self.start_time = datetime.datetime.now()
    
    def draw(self):
        screen.fill(BLACK)
        self.bird.draw()
        for pipe in self.pipes:
            pipe.draw()
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        pygame.display.flip()
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)

if __name__ == "__main__":
    game = Game()
    game.run()
'''

# Write updated game.py
game_path = os.path.join(project_folder, "game.py")
with open(game_path, "w") as f:
    f.write(game_code)
print(f"Updated game.py at: {game_path}")

if not os.path.exists(game_path):
    print("Error: game.py was not created!")
    sys.exit(1)