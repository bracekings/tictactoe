# Example file showing a circle moving on screen
import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("blue")

    pygame.draw.circle(screen, "red", player_pos, 40)

#moving character via drag and drop functionality
    if pygame.mouse.get_pressed()[0]:  # Check if left mouse button is pressed
        mouse_pos = pygame.mouse.get_pos()  # Get the current mouse position
        player_pos.update(mouse_pos)  # Update player position to mouse position
    #making sure player only moves when mouse is clicked on the player
    
#creating start and stop pannel
    start_button = pygame.Rect(10, 10, 100, 50)
    stop_button = pygame.Rect(120, 10, 100, 50)

    pygame.draw.rect(screen, "green", start_button)
    pygame.draw.rect(screen, "red", stop_button)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
