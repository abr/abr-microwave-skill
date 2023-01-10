import datetime
import json
import sys

import pygame
import glob

# Initialize pygame and create a screen
pygame.init()
path_to_mwave_image = "/opt/mycroft/skills/abr-microwave-skill/display/mwave.jpg"
path_to_mwave_off_image = (
    "/opt/mycroft/skills/abr-microwave-skill/display/mwave_off.jpg"
)
path_to_message_doc = "/home/nani/.config/mycroft/skills/AbrMicrowave/messages.json"
WIDTH = 1237    
HEIGHT = 708
FONT_SIZE = 40
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# timer font
font = pygame.font.Font("/opt/mycroft/skills/abr-microwave-skill/display/digital.tff", FONT_SIZE)
# heat mode font
font_mode = pygame.font.Font("/opt/mycroft/skills/abr-microwave-skill/display/calibril.ttf", 16)
# type font
font_type = pygame.font.Font("/opt/mycroft/skills/abr-microwave-skill/display/calibril.ttf", 16)

# Define a function for rendering text to the screen
def render_text(state):

    status = state["status"]

    # create a surface object to cover up a portion of the image
    height = 240
    width = 140
    surface = pygame.Surface((width, height))
    surface.fill((17 , 12, 8))
    surface_x = 1062
    surface_y = 148
    screen.blit(surface, (surface_x, surface_y))
    

    # timer
    height = 40
    width = 140
    time_surface = pygame.Surface((width, height))
    #time_surface.fill((17 , 12, 8))
    time_surface.fill((27 , 26, 21))
    surface_x = 1062
    surface_y = 160
    screen.blit(time_surface, (surface_x, surface_y))
    time_text = font.render(str(datetime.timedelta(seconds=state["timer"])), True, (255, 255, 255))
    text_x = surface_x + (width - time_text.get_width()) // 2
    text_y = surface_y + (height - time_text.get_height()) // 2
    screen.blit(time_text, (text_x, text_y))

    # Heat mode
    mode = state["heat_mode"] if status == 1 else " "
    mode_text = font_mode.render(mode.title(), True, (255, 255, 255))
    height = 31
    width = 68.5
    mode_surface = pygame.Surface((width, height))
    mode_surface.fill((27 , 26, 21))
    surface_x = 1062
    surface_y = 210
    screen.blit(mode_surface, (surface_x, surface_y))
    text_x = surface_x + (width - mode_text.get_width()) // 2
    text_y = surface_y + (height - mode_text.get_height()) // 2
    screen.blit(mode_text, (text_x, text_y))

    # type
    type = state["type"]
    type = type if status == 1 and type is not None else " "
    type_text = font_type.render(type.title(), True, (255, 255, 255))
    height = 31
    width = 68.5
    type_surface = pygame.Surface((width, height))
    type_surface.fill((27 , 26, 21))
    surface_x = surface_x + width + 5
    surface_y = 210
    screen.blit(mode_surface, (surface_x, surface_y))
    text_x = surface_x + (width - type_text.get_width()) // 2
    text_y = surface_y + (height - type_text.get_height()) // 2

    screen.blit(type_text, (text_x, text_y))

# class Player(pygame.sprite.Sprite):
#     def __init__(self, pos_x, pos_y):
#         super().__init__()
#         self.attack_animation = False
#         self.sprites = []
#         all_im_paths = glob.glob('/home/nani/Desktop/animation-master/*.png')
#         for path in all_im_paths:
#             self.sprites.append(pygame.image.load(path))
#         self.current_sprite = 0
#         self.image = self.sprites[self.current_sprite]

#         self.rect = self.image.get_rect()
#         self.rect.topleft = [pos_x,pos_y]

#     def attack(self):
#         self.attack_animation = True

#     def update(self,speed):
#         if self.attack_animation == True:
#             self.current_sprite += speed
#             if int(self.current_sprite) >= len(self.sprites):
#                 self.current_sprite = 0
#                 self.attack_animation = False

#         self.image = self.sprites[int(self.current_sprite)]


# Creating the sprites and groups
#moving_sprites = pygame.sprite.Group()
#player = Player(1080,300)
#moving_sprites.add(player)

# Run the main loop until the user quits
while True:
    # Check for events
    for event in pygame.event.get():
        print(event)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # if event.type == pygame.KEYDOWN:
        #     player.attack()

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
    #moving_sprites.draw(screen)
    #moving_sprites.update(0.05)
    pygame.display.flip()
