import datetime
import json
import sys

import pygame

# Initialize pygame and create a screen
pygame.init()
path_to_mwave_image = "/opt/mycroft/skills/abr-microwave-skill/display/mwave.png"
path_to_mwave_off_image = (
    "/opt/mycroft/skills/abr-microwave-skill/display/mwave_off.jpg"
)
path_to_message_doc = "/opt/mycroft/skills/abr-microwave-skill/display/messages.json"
WIDTH = 1269
HEIGHT = 908
FONT_SIZE = 62
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# timer font
font = pygame.font.Font(None, FONT_SIZE)
# heat mode font
font_mode = pygame.font.Font(None, 27)
# type font
font_type = pygame.font.Font(None, 27)

# Define a function for rendering text to the screen
def render_text(state):

    status = state["status"]

    # Create a Surface object for the timer
    time = str(datetime.timedelta(seconds=state["timer"]))
    text_surface = font.render(time, True, (255, 255, 255))
    screen.blit(text_surface, (981, 185))

    # Heat mode
    mode = state["heat_mode"] if status == 1 else " "
    mode_text = font_mode.render(mode.title(), True, (255, 255, 255))
    height = 31
    width = 76
    mode_surface = pygame.Surface((width, height))
    mode_surface.fill((0, 0, 0))
    surface_x = 979
    surface_y = 240
    screen.blit(mode_surface, (surface_x, surface_y))
    text_x = surface_x + (width - mode_text.get_width()) // 2
    text_y = surface_y + (height - mode_text.get_height()) // 2
    screen.blit(mode_text, (text_x, text_y))

    # type
    type = state["type"]
    type = type if status == 1 and type is not None else " "
    type_text = font_type.render(type.title(), True, (255, 255, 255))
    height = 31
    width = 74
    type_surface = pygame.Surface((width, height))
    type_surface.fill((0, 0, 0))
    surface_x = 1057
    surface_y = 240
    screen.blit(mode_surface, (surface_x, surface_y))
    text_x = surface_x + (width - type_text.get_width()) // 2
    text_y = surface_y + (height - type_text.get_height()) // 2

    screen.blit(type_text, (text_x, text_y))


# Run the main loop until the user quits
while True:
    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    with open(path_to_message_doc) as file:
        state = json.load(file)

    # Load the icon image
    mwave = pygame.Surface((WIDTH, HEIGHT))
    if state["status"] == 1:
        image = pygame.image.load(path_to_mwave_image)
    else:
        image = pygame.image.load(path_to_mwave_off_image)

    mwave.blit(image, (0, 0))
    screen.blit(image, (0, 0))

    render_text(state)

    pygame.display.flip()
