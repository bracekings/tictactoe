import pygame
import random
from sys import exit

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Game")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Font
font = pygame.font.Font(None, 36)

# Button sizes
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50

# Start button (centered)
start_button = pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 - 70, BUTTON_WIDTH, BUTTON_HEIGHT)

# Control button (below start button)
control_button = pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 + 10, BUTTON_WIDTH, BUTTON_HEIGHT)

# Player setup
player = pygame.Rect(25, 25, 25, 25)

# Enemy setup (initialized later)
enemy = None  # placeholder

# Game state
game_state = 'menu'

# Function to spawn enemy away from player
def spawn_enemy_away_from_player(player_rect, min_distance=150):
    while True:
        x = random.randint(0, WIDTH - 25)
        y = random.randint(0, HEIGHT - 25)
        enemy_rect = pygame.Rect(x, y, 25, 25)
        dx = enemy_rect.centerx - player_rect.centerx
        dy = enemy_rect.centery - player_rect.centery
        if dx**2 + dy**2 >= min_distance**2:
            return enemy_rect

#inventory bar
inventory_bar = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)

#draw inventory 

# Clock
clock = pygame.time.Clock()
running = True

# Game loop
while running:
    # Fill background depending on state
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # Handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == 'menu':
                if start_button.collidepoint(event.pos):
                    game_state = 'game'
                    player = pygame.Rect(25, 25, 25, 25)  # reset player
                    enemy = spawn_enemy_away_from_player(player)
                elif control_button.collidepoint(event.pos):
                    print("Control button clicked!")  # You can add more functionality here

    # MENU SCREEN
    if game_state == 'menu':
        mouse_pos = pygame.mouse.get_pos()

        # --- Start Button ---
        hovering_start = start_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, GREEN if hovering_start else WHITE, start_button)
        start_text = font.render("START", True, BLACK)
        screen.blit(start_text, (start_button.x + 70, start_button.y + 10))

        # --- Control Button ---
        hovering_control = control_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, GREEN if hovering_control else WHITE, control_button)
        control_text = font.render("CONTROL", True, BLACK)
        screen.blit(control_text, (control_button.x + 55, control_button.y + 10))

    # GAME SCREEN
    elif game_state == 'game':
        # Draw player
        pygame.draw.rect(screen, BLUE, player)

        # Draw enemy
        if enemy:
            pygame.draw.rect(screen, RED, enemy)

        # Handle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= 5
        if keys[pygame.K_RIGHT]:
            player.x += 5
        if keys[pygame.K_UP]:
            player.y -= 5
        if keys[pygame.K_DOWN]:
            player.y += 5
        if keys[pygame.K_ESCAPE]:
            game_state = 'menu'

    # Update display and tick
    pygame.display.flip()
    clock.tick(60)
