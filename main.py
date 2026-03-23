import pygame
from room import Room
from player import Player

pygame.init()

SCREEN_W = 800
SCREEN_H = 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Mon jeu")
clock = pygame.time.Clock()

room = Room("assets/maps/premiere salle donjon.tmx")
player = Player(300, 300)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update()
    player_rect = pygame.Rect(player.x, player.y, 48, 64)
    collected = room.check_items(player_rect)
    for item in collected:
        print(f"Ramassé : {item}")

    screen.fill((0, 0, 0))
    room.draw(screen)
    player.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
pygame.quit()