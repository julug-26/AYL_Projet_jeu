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

controls1 = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN
}
controls2 = {
    "left": pygame.K_q,
    "right": pygame.K_d,
    "up": pygame.K_z,
    "down": pygame.K_s
}

player1 = Player(300, 300, "assets/spritepersobleu.png", controls1)
player2 = Player(200, 300, "assets/spritepersovert.png", controls2)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player1.update()
    player2.update()

    p1_rect = pygame.Rect(player1.x, player1.y, 48, 64)
    p2_rect = pygame.Rect(player2.x, player2.y, 48, 64)

    for rect in [p1_rect, p2_rect]:
        collected = room.check_items(rect)
        for item in collected:
            print(f"Ramassé : {item}")

    screen.fill((0, 0, 0))
    room.draw(screen)
    player1.draw(screen)
    player2.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()