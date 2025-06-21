import os
import subprocess
import sys

# Project setup
project_name = "snake_game"
project_folder = os.path.expanduser(f"~/Desktop/Work/{project_name}")

# Create project directory if it doesn't exist
os.makedirs(project_folder, exist_ok=True)

# Create logs.txt file
logs_path = os.path.join(project_folder, "logs.txt")
with open(logs_path, "w") as f:
    f.write("Snake Game Score Log\n")
print(f"Created logs.txt at: {logs_path}")

# Modify game.py to add logging
game_code = '''
import pygame
import random
import datetime

# Initialize Pygame
pygame.init()

# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BLOCK_SIZE = 20

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Initialize game window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Game")

# Snake class
class Snake:
    def __init__(self):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        self.dx = BLOCK_SIZE
        self.dy = 0
        self.body = [(self.x, self.y)]
        self.length = 1
        self.score = 0

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.body.insert(0, (self.x, self.y))
        if len(self.body) > self.length:
            self.body.pop()

    def check_collision(self):
        # Wall collision
        if (self.x < 0 or self.x >= WINDOW_WIDTH or 
            self.y < 0 or self.y >= WINDOW_HEIGHT):
            return True
        
        # Self collision
        if (self.x, self.y) in self.body[1:]:
            return True
        
        return False

# Food class
class Food:
    def __init__(self):
        self.spawn()

    def spawn(self):
        self.x = random.randrange(0, WINDOW_WIDTH - BLOCK_SIZE, BLOCK_SIZE)
        self.y = random.randrange(0, WINDOW_HEIGHT - BLOCK_SIZE, BLOCK_SIZE)

def log_score(score):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs.txt", "a") as f:
        f.write(f"{timestamp} - Score: {score}\\n")

def main():
    clock = pygame.time.Clock()
    snake = Snake()
    food = Food()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                log_score(snake.score)
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and snake.dx == 0:
                    snake.dx = -BLOCK_SIZE
                    snake.dy = 0
                elif event.key == pygame.K_RIGHT and snake.dx == 0:
                    snake.dx = BLOCK_SIZE
                    snake.dy = 0
                elif event.key == pygame.K_UP and snake.dy == 0:
                    snake.dx = 0
                    snake.dy = -BLOCK_SIZE
                elif event.key == pygame.K_DOWN and snake.dy == 0:
                    snake.dx = 0
                    snake.dy = BLOCK_SIZE

        # Move snake
        snake.move()

        # Check collision
        if snake.check_collision():
            log_score(snake.score)
            running = False

        # Check food collision
        if snake.x == food.x and snake.y == food.y:
            snake.length += 1
            snake.score += 10
            food.spawn()

        # Draw everything
        window.fill(BLACK)
        
        # Draw snake
        for segment in snake.body:
            pygame.draw.rect(window, GREEN, 
                           (segment[0], segment[1], BLOCK_SIZE, BLOCK_SIZE))

        # Draw food
        pygame.draw.rect(window, RED, 
                        (food.x, food.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {snake.score}', True, WHITE)
        window.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(10)

    pygame.quit()

if __name__ == '__main__':
    main()
'''

# Write updated game.py
game_path = os.path.join(project_folder, "game.py")
with open(game_path, "w") as f:
    f.write(game_code)
print(f"Updated game.py at: {game_path}")

if not os.path.exists(game_path):
    print("Error: game.py was not created!")
    sys.exit(1)