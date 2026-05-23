import pygame
from room import Room
from player import Player
from menu import main_menu

# Lancement du menu
mode = main_menu()

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("assets/jean-paul-v-au-chateau-de-langeais-307767.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

FPS = 60
screen = pygame.display.set_mode((1, 1))

temp_room = Room("assets/maps/premiere salle donjon.tmx")
SCREEN_W = temp_room.data.width * temp_room.data.tilewidth
SCREEN_H = temp_room.data.height * temp_room.data.tileheight

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Mon jeu")
clock = pygame.time.Clock()

rooms = {
    "salle1": temp_room,
    "salle2": Room("assets/maps/map 2.tmx"),
    "salle3": Room("assets/maps/salle_3.tmx")
}
rooms["salle3"].both_plaques_required = True

current_room_key = "salle1"
room = rooms[current_room_key]

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

spawn1 = rooms["salle1"].spawn
player1 = Player(spawn1[0] if spawn1 else 300, spawn1[1] if spawn1 else 300, "assets/spritepersobleu.png", controls1)
player2 = Player((spawn1[0] + 50) if spawn1 else 200, spawn1[1] if spawn1 else 300, "assets/spritepersovert.png", controls2)

font = pygame.font.SysFont(None, 36)
notification = None
notification_timer = 0

running = True
while running:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_m:
                p1_rect = pygame.Rect(player1.x, player1.y, 48, 64)
                room.activate_levier(p1_rect, "levier 1")
                room.activate_levier(p1_rect, "levier 2")
            if event.key == pygame.K_e:
                p2_rect = pygame.Rect(player2.x, player2.y, 48, 64)
                room.activate_levier(p2_rect, "levier 1")
                room.activate_levier(p2_rect, "levier 2")

    player1.update(room.collisions)
    player2.update(room.collisions)

    p1_rect = pygame.Rect(player1.x, player1.y, 48, 64)
    p2_rect = pygame.Rect(player2.x, player2.y, 48, 64)

    for rect in [p1_rect, p2_rect]:
        collected = room.check_items(rect)
        for item in collected:
            notification = f"Ramassé : {item}"
            notification_timer = 3000

    door_status, door_info = room.check_doors(p1_rect, p2_rect)
    room.check_plaques(p1_rect, p2_rect)

    if door_status == "both" and door_info:
        current_room_key = door_info
        room = rooms[current_room_key]
        if room.spawn:
            player1.x, player1.y = room.spawn[0], room.spawn[1]
            player2.x, player2.y = room.spawn[0] + 50, room.spawn[1]
        else:
            player1.x, player1.y = 300, 300
            player2.x, player2.y = 200, 300
        notification = None
    elif door_status == "one":
        notification = "Les deux joueurs doivent atteindre la porte de sortie !"
        notification_timer = 3000

    screen.fill((0, 0, 0))
    room.draw(screen, dt, p1_rect, p2_rect)
    player1.draw(screen)
    player2.draw(screen)

    if notification and notification_timer > 0:
        notification_timer -= dt * 4
        small_font = pygame.font.SysFont(None, 24)
        text = small_font.render(notification, True, (255, 255, 255))
        pad = 10
        rect_w = text.get_width() + pad * 2
        rect_h = text.get_height() + pad * 2
        rect_x = SCREEN_W // 2 - rect_w // 2
        rect_y = SCREEN_H // 2 - rect_h // 2
        notif_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        notif_surf.fill((30, 30, 30, 120))
        screen.blit(notif_surf, (rect_x, rect_y))
        pygame.draw.rect(screen, (255, 255, 255, 80), (rect_x, rect_y, rect_w, rect_h), 1, border_radius=6)
        screen.blit(text, (rect_x + pad, rect_y + pad))

    pygame.display.flip()

pygame.quit()