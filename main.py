import pygame
import argparse
from room import Room
from player import Player
from menu import main_menu
from network import NetworkClient
from server import GameServer
from enemy import RoomEnemy, BossEnemy

parser = argparse.ArgumentParser(description="What's Next")
parser.add_argument("--network", choices=("local", "client"), default="local")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=5555)
args = parser.parse_args()

network_client = None
local_server = None
local_player_id = None
last_network_event_id = 0

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
    "salle3": Room("assets/maps/salle_3.tmx"),
    "salle4": Room("assets/maps/salle_4.tmx")
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
PLAYER1_ATTACK_KEYS = (pygame.K_RCTRL, pygame.K_KP0)
PLAYER2_ATTACK_KEYS = (pygame.K_f,)
NETWORK_ATTACK_KEYS = PLAYER1_ATTACK_KEYS + PLAYER2_ATTACK_KEYS + (pygame.K_SPACE,)

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
            players[local_player_id].controls = controls2
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
SHORT_NOTIFICATION_MS = 2500
LONG_NOTIFICATION_MS = 5000
salle4_enemies = []
salle4_boss_spawned = False

def player_rect(player):
    return pygame.Rect(player.x, player.y, 48, 64)

def activate_local_leviers(player):
    rect = player_rect(player)
    room.activate_levier(rect, "levier 1")
    room.activate_levier(rect, "levier 2")

def reset_room_state(room_key):
    global salle4_enemies, salle4_boss_spawned
    rooms[room_key].reset_state()
    if room_key == "salle4":
        salle4_enemies = [
            RoomEnemy(90, 230, target_player=0, hp=45, speed=1.3, color=(210, 65, 55)),
            RoomEnemy(520, 165, target_player=1, hp=45, speed=1.3, color=(210, 65, 55)),
        ]
        salle4_boss_spawned = False

def set_players_on_room_spawn(room_key):
    target_room = rooms[room_key]
    p1_spawn = target_room.spawn_points.get("spawn J1 salle 4", target_room.spawn)
    p2_spawn = target_room.spawn_points.get("spawn J2 salle 4", target_room.spawn)
    if p1_spawn:
        player1.x, player1.y = p1_spawn
    else:
        player1.x, player1.y = 300, 300
    if p2_spawn:
        player2.x, player2.y = p2_spawn
    elif p1_spawn:
        player2.x, player2.y = p1_spawn[0] + 50, p1_spawn[1]
    else:
        player2.x, player2.y = 200, 300
    player1.hp = 100
    player2.hp = 100
    player1.invulnerability_timer = 0
    player2.invulnerability_timer = 0

def damage_enemies(attacking_players):
    global notification, notification_timer
    if current_room_key != "salle4":
        return

    for player in attacking_players:
        attack_rect = player.rect.inflate(34, 34)
        for enemy in salle4_enemies:
            if enemy.alive and attack_rect.colliderect(enemy.rect):
                enemy.take_damage(20)
                notification = "Ennemi touche !"
                notification_timer = SHORT_NOTIFICATION_MS
                return

def update_salle4_enemies():
    global salle4_boss_spawned, salle4_enemies
    if current_room_key != "salle4":
        return

    opened = room.levier1_activated and room.levier2_activated
    if opened and not salle4_boss_spawned:
        salle4_enemies = []
        salle4_enemies.append(BossEnemy(305, 90))
        salle4_boss_spawned = True

    active_players = [player1, player2]
    room_bounds = pygame.Rect(0, 0, SCREEN_W, SCREEN_H)
    for enemy in salle4_enemies:
        enemy.update(room.collisions, active_players, room_bounds)
    salle4_enemies = [enemy for enemy in salle4_enemies if enemy.alive]

def draw_salle4_enemies(surface, dt):
    if current_room_key != "salle4":
        return
    for enemy in salle4_enemies:
        enemy.draw(surface, dt)

def show_credits():
    credits_font = pygame.font.SysFont(None, 46)
    title_font = pygame.font.SysFont(None, 64)
    names = ["Nael Belhadj Amara", "Melissa Gay", "Julia Guimaraes", "Hadrien Beaurepaire", "Ghali Bennani"]
    lines = ["Merci d'avoir joué", "", "Equipe"] + names + ["", "Fin"]
    scroll_y = SCREEN_H
    running_credits = True

    while running_credits:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                return

        screen.fill((0, 0, 0))
        y = scroll_y
        for index, line in enumerate(lines):
            font_to_use = title_font if index == 0 else credits_font
            text = font_to_use.render(line, True, (230, 240, 230))
            screen.blit(text, text.get_rect(center=(SCREEN_W // 2, int(y))))
            y += 62

        scroll_y -= dt * 0.04
        if y < 0:
            running_credits = False
        pygame.display.flip()

def restart_current_room():
    global notification, notification_timer
    reset_room_state(current_room_key)
    set_players_on_room_spawn(current_room_key)
    notification = "Un joueur est tombe ! Salle recommencee."
    notification_timer = LONG_NOTIFICATION_MS

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
            if args.network == "client" and event.key in NETWORK_ATTACK_KEYS:
                if local_player_id:
                    damage_enemies([players[local_player_id]])
            elif args.network != "client":
                if event.key in PLAYER1_ATTACK_KEYS:
                    damage_enemies([player1])
                if event.key in PLAYER2_ATTACK_KEYS:
                    damage_enemies([player2])
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
            notification_timer = LONG_NOTIFICATION_MS

    door_status, door_info = room.check_doors(p1_rect, p2_rect)
    room.check_plaques(p1_rect, p2_rect)
    update_salle4_enemies()
    if current_room_key == "salle4" and salle4_boss_spawned and not salle4_enemies:
        show_credits()
        running = False
        continue

    room_restarted = player1.hp <= 0 or player2.hp <= 0
    if room_restarted:
        restart_current_room()
        p1_rect = player_rect(player1)
        p2_rect = player_rect(player2)

    if not room_restarted and door_status == "both" and door_info:
        current_room_key = door_info
        room = rooms[current_room_key]
        set_players_on_room_spawn(current_room_key)
        reset_room_state(current_room_key)
        notification = None
    elif not room_restarted and door_status == "one":
        notification = "Les deux joueurs doivent atteindre la porte de sortie !"
        notification_timer = LONG_NOTIFICATION_MS

    screen.fill((0, 0, 0))
    room.draw(screen, dt, p1_rect, p2_rect)
    draw_salle4_enemies(screen, dt)
    player1.draw(screen)
    player2.draw(screen)

    if notification and notification_timer > 0:
        notification_timer -= dt
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
