import os
import sys
import subprocess

def main():
    # Define project name and paths
    project_name = "flappy_bird"
    base_dir = os.path.expanduser("~/Desktop/Work")
    project_dir = os.path.join(base_dir, project_name)
    venv_dir = os.path.join(project_dir, "venv")
    main_py = os.path.join(project_dir, "main.py")

    # Step 1: Project Setup - Create project directory
    os.makedirs(project_dir, exist_ok=True)

    # Step 2: Dependency Installation - Create virtual environment
    subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Step 3: Dependency Installation - Install pygame in the venv
    pip_path = os.path.join(venv_dir, "bin", "pip") if os.name != "nt" else os.path.join(venv_dir, "Scripts", "pip.exe")
    subprocess.run([pip_path, "install", "pygame"], check=True)

    # Step 4: Feature Implementation - Write Flappy Bird game to main.py
    flappy_code = '''import pygame
import sys
import random

# Game Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GROUND_HEIGHT = 100
BIRD_WIDTH = 34
BIRD_HEIGHT = 24
PIPE_WIDTH = 52
PIPE_HEIGHT = 320
PIPE_GAP = 150
GRAVITY = 0.25
JUMP_STRENGTH = -6.5
FPS = 60

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)

def draw_text(text, x, y):
    img = font.render(text, True, (255,255,255))
    rect = img.get_rect(center=(x, y))
    screen.blit(img, rect)

def load_bird():
    surf = pygame.Surface((BIRD_WIDTH, BIRD_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (255,255,0), [0,0,BIRD_WIDTH,BIRD_HEIGHT])
    pygame.draw.circle(surf, (255,0,0), (int(BIRD_WIDTH*0.75), int(BIRD_HEIGHT/2)), 3)
    return surf

def load_pipe():
    surf = pygame.Surface((PIPE_WIDTH, PIPE_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surf, (0,255,0), [0,0,PIPE_WIDTH,PIPE_HEIGHT])
    pygame.draw.rect(surf, (0,200,0), [0,0,PIPE_WIDTH,30])
    return surf

def main():
    bird = load_bird()
    pipe_img = load_pipe()
    bird_x = 50
    bird_y = SCREEN_HEIGHT//2
    bird_vel = 0
    pipes = []
    score = 0
    running = True
    game_over = False

    def reset():
        nonlocal bird_y, bird_vel, pipes, score, game_over
        bird_y = SCREEN_HEIGHT//2
        bird_vel = 0
        pipes = []
        score = 0
        game_over = False

    SPAWNPIPE = pygame.USEREVENT
    pygame.time.set_timer(SPAWNPIPE, 1200)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bird_vel = JUMP_STRENGTH
                if event.key == pygame.K_SPACE and game_over:
                    reset()
            if event.type == SPAWNPIPE and not game_over:
                pipe_height = random.randint(80, SCREEN_HEIGHT - GROUND_HEIGHT - PIPE_GAP - 80)
                pipes.append({'x': SCREEN_WIDTH, 'top': pipe_height, 'passed': False})

        if not game_over:
            bird_vel += GRAVITY
            bird_y += bird_vel

            # Pipes movement
            for pipe in pipes:
                pipe['x'] -= 3

            # Remove off-screen pipes
            pipes = [p for p in pipes if p['x'] > -PIPE_WIDTH]

            # Collision detection
            bird_rect = pygame.Rect(bird_x, int(bird_y), BIRD_WIDTH, BIRD_HEIGHT)
            for pipe in pipes:
                top_rect = pygame.Rect(pipe['x'], 0, PIPE_WIDTH, pipe['top'])
                bottom_rect = pygame.Rect(pipe['x'], pipe['top']+PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT-GROUND_HEIGHT-(pipe['top']+PIPE_GAP))
                if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                    game_over = True
                if not pipe['passed'] and pipe['x'] + PIPE_WIDTH < bird_x:
                    score += 1
                    pipe['passed'] = True

            # Ground and ceiling collision
            if bird_y < 0 or bird_y + BIRD_HEIGHT > SCREEN_HEIGHT - GROUND_HEIGHT:
                game_over = True

        # Drawing
        screen.fill((0,0,80))
        # Pipes
        for pipe in pipes:
            screen.blit(pipe_img, (pipe['x'], pipe['top']-PIPE_HEIGHT))
            screen.blit(pygame.transform.flip(pipe_img, False, True), (pipe['x'], pipe['top']+PIPE_GAP))
        # Ground
        pygame.draw.rect(screen, (222, 184, 135), [0, SCREEN_HEIGHT-GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT])
        # Bird
        screen.blit(bird, (bird_x, int(bird_y)))
        # Score
        draw_text(str(score), SCREEN_WIDTH//2, 50)
        if game_over:
            draw_text("Game Over", SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            draw_text("Press SPACE to restart", SCREEN_WIDTH//2, SCREEN_HEIGHT//2+50)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
'''
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(flappy_code)

if __name__ == "__main__":
    main()