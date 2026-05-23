import pygame
import argparse
from room import Room
from player import Player
from menu import main_menu
from network import NetworkClient
from server import GameServer

parser = argparse.ArgumentParser(description="What's Next")
parser.add_argument("--network", choices=("local", "client"), default="local")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=5555)
args = parser.parse_args()

network_client = None
local_server = None
local_player_id = None
last_network_event_id = 0

# Lancement du menu
mode = main_menu()
if isinstance(mode, dict):
    if mode.get("mode") == "host":
        args.network = "client"
        args.host = "127.0.0.1"
    elif mode.get("mode") == "join":
        args.network = "client"
        args.host = mode.get("host", "127.0.0.1")
    else:
        args.network = "local"

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
fullscreen = True

def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    flags = pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

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
players = {
    "player1": player1,
    "player2": player2,
}

if args.network == "client":
    if isinstance(mode, dict) and mode.get("mode") == "host":
        local_server = GameServer(port=args.port)
        local_server.start_in_background()
    network_client = NetworkClient(args.host, args.port)
    try:
        network_client.connect()
        wait_start = pygame.time.get_ticks()
        while network_client.connected and not network_client.player_id:
            if pygame.time.get_ticks() - wait_start > 5000:
                break
            pygame.time.wait(10)
        local_player_id = network_client.player_id
        if local_player_id:
            players[local_player_id].controls = controls1
            print(f"Connecte au serveur comme {local_player_id}")
        else:
            print("Connexion impossible: aucun joueur attribue par le serveur")
            network_client.close()
            network_client = None
            args.network = "local"
    except OSError as error:
        print(f"Connexion impossible au serveur {args.host}:{args.port}: {error}")
        network_client = None
        args.network = "local"

font = pygame.font.SysFont(None, 36)
notification = None
notification_timer = 0

def player_rect(player):
    return pygame.Rect(player.x, player.y, 48, 64)

def activate_local_leviers(player):
    rect = player_rect(player)
    room.activate_levier(rect, "levier 1")
    room.activate_levier(rect, "levier 2")

running = True
while running:
    dt = clock.tick(FPS)
    network_event = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                running = False
            if args.network == "client":
                if event.key in (pygame.K_e, pygame.K_m) and local_player_id:
                    activate_local_leviers(players[local_player_id])
                    network_event = "interact"
            else:
                if event.key == pygame.K_m:
                    activate_local_leviers(player1)
                if event.key == pygame.K_e:
                    activate_local_leviers(player2)

    if args.network == "client" and local_player_id:
        players[local_player_id].update(room.collisions)

        state = network_client.get_state()
        for player_id, player_state in state["players"].items():
            if player_id != local_player_id and player_id in players:
                players[player_id].apply_network_state(player_state)

        for net_event in state["events"]:
            if net_event.get("id", 0) <= last_network_event_id:
                continue
            last_network_event_id = net_event.get("id", last_network_event_id)
            event_player_id = net_event.get("player_id")
            if event_player_id != local_player_id and event_player_id in players:
                if net_event.get("type") == "interact":
                    activate_local_leviers(players[event_player_id])

        network_client.send_player_state(
            players[local_player_id].to_network_state(),
            network_event,
        )
    else:
        player1.update(room.collisions)
        player2.update(room.collisions)

    p1_rect = player_rect(player1)
    p2_rect = player_rect(player2)

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

if network_client:
    network_client.close()
if local_server:
    local_server.stop()
pygame.quit()
