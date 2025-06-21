import os
import subprocess
import sys

# Project setup
project_name = "flappy_bird"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory
os.makedirs(project_folder, exist_ok=True)

# Create logs.txt file
logs_path = os.path.join(project_folder, "logs.txt")
if not os.path.exists(logs_path):
    with open(logs_path, "w") as f:
        f.write("Flappy Bird Game Results\n")
    print(f"Created logs file at: {logs_path}")

# Modify game.py to add logging functionality
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
    
    def flap(self):
        self.velocity = FLAP_STRENGTH
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.y = self.y
    
    def draw(self):
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
        self.last_pipe = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)
        self.start_time = datetime.datetime.now()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.log_game_result()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.bird.flap()
    
    def update(self):
        self.bird.update()
        
        # Spawn new pipes
        now = pygame.time.get_ticks()
        if now - self.last_pipe > PIPE_FREQUENCY:
            self.pipes.append(Pipe())
            self.last_pipe = now
        
        # Update and remove pipes
        for pipe in self.pipes[:]:
            pipe.update()
            if pipe.x < -50:
                self.pipes.remove(pipe)
            if not pipe.passed and pipe.x < self.bird.x:
                pipe.passed = True
                self.score += 1
        
        # Check collisions
        for pipe in self.pipes:
            if pipe.top_rect.colliderect(self.bird.rect) or pipe.bottom_rect.colliderect(self.bird.rect):
                self.log_game_result()
                return True
        
        # Check boundaries
        if self.bird.y < 0 or self.bird.y > SCREEN_HEIGHT:
            self.log_game_result()
            return True
            
        return False
    
    def draw(self):
        screen.fill(BLACK)
        self.bird.draw()
        for pipe in self.pipes:
            pipe.draw()
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        pygame.display.flip()
    
    def log_game_result(self):
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        log_entry = f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] Score: {self.score}, Duration: {duration:.2f}s\\n"
        with open("logs.txt", "a") as f:
            f.write(log_entry)

def main():
    game = Game()
    running = True
    
    while running:
        game.handle_events()
        game_over = game.update()
        game.draw()
        
        if game_over:
            running = False
        
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
'''

# Write game.py to project directory
game_path = os.path.join(project_folder, "game.py")
with open(game_path, "w") as f:
    f.write(game_code)
print(f"Updated game.py with logging functionality at: {game_path}")
if not os.path.exists(game_path):
    print("Error: game.py was not created!")
    sys.exit(1)