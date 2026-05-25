import pygame
import argparse
from room import Room
from player import Player, J1_ANIM_MAP, J2_ANIM_MAP
from menu import main_menu
from network import NetworkClient
from server import GameServer
from enemy import RoomEnemy, BossEnemy, ScorpioEnemy, ScorpioBoss

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

SALLE5_W = 960
SALLE5_H = 640

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Mon jeu")
clock = pygame.time.Clock()
fullscreen = True


def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    flags = pygame.FULLSCREEN if fullscreen else pygame.NOFRAME
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

rooms = {
    "salle1": temp_room,
    "salle2": Room("assets/maps/map 2.tmx"),
    "salle3": Room("assets/maps/salle_3.tmx"),
    "salle4": Room("assets/maps/salle_4.tmx"),
    "salle5": Room("assets/maps/salle_5.tmx"),
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
player1 = Player(spawn1[0] if spawn1 else 300, spawn1[1] if spawn1 else 300, "sprite/sprite_j1 copy", controls1, anim_map=J1_ANIM_MAP)
player2 = Player((spawn1[0] + 50) if spawn1 else 200, spawn1[1] if spawn1 else 300, "sprite/sprite_j2/sprite_j2", controls2, anim_map=J2_ANIM_MAP)
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
salle4_enemies = []
salle4_boss_spawned = False
salle5_enemies = []
salle5_wave1_spawned = False
salle5_wave2_spawned = False
salle5_wave3_spawned = False
salle5_wave4_spawned = False
salle5_bosses_spawned = False
controls_timer = 10000
remote_enemies = []  # ennemis reçus du réseau (client seulement)
both_door_frames = 0  # compteur de frames où les deux joueurs sont à la porte

def _serialize_enemies():
    """Sérialise tous les ennemis actifs en liste de dicts pour le réseau."""
    result = []
    enemy_list = salle4_enemies if current_room_key == "salle4" else salle5_enemies if current_room_key == "salle5" else []
    for e in enemy_list:
        result.append({
            "type": type(e).__name__,
            "x": e.rect.x,
            "y": e.rect.y,
            "hp": e.hp,
            "max_hp": e.max_hp,
            "alive": e.alive,
            "state": e.state,
            "anim_frame": e.anim_frame,
            "flip": e.flip,
            "projectiles": [
                {"x": p.rect.x, "y": p.rect.y}
                for p in getattr(e, "projectiles", [])
            ],
        })
    return result

def player_rect(player):
    return pygame.Rect(player.x, player.y, 48, 64)

def activate_local_leviers(player):
    rect = player_rect(player)
    room.activate_levier(rect, "levier 1")
    room.activate_levier(rect, "levier 2")
    room.activate_levier(rect, "levier 3")

def reset_room_state(room_key):
    global salle4_enemies, salle4_boss_spawned
    global salle5_enemies, salle5_wave1_spawned, salle5_wave2_spawned
    global salle5_wave3_spawned, salle5_wave4_spawned, salle5_bosses_spawned
    rooms[room_key].reset_state()
    if room_key == "salle4":
        salle4_enemies = [
            RoomEnemy(90, 230, target_player=0, hp=45, speed=1.3, color=(210, 65, 55)),
            RoomEnemy(520, 165, target_player=1, hp=45, speed=1.3, color=(210, 65, 55)),
        ]
        salle4_boss_spawned = False
    if room_key == "salle5":
        salle5_enemies = []
        salle5_wave1_spawned = False
        salle5_wave2_spawned = False
        salle5_wave3_spawned = False
        salle5_wave4_spawned = False
        salle5_bosses_spawned = False

def spawn_enemy_at(spawn_name, target_room, scorpio=False):
    sp = target_room.spawn_points.get(spawn_name)
    if sp:
        if scorpio:
            return ScorpioEnemy(sp[0], sp[1], hp=45, speed=1.3)
        return RoomEnemy(sp[0], sp[1], hp=45, speed=1.3, color=(210, 65, 55))
    return None

def spawn_boss_at(spawn_name, target_room):
    sp = target_room.spawn_points.get(spawn_name)
    if sp:
        return BossEnemy(sp[0], sp[1])
    return None

def set_players_on_room_spawn(room_key):
    target_room = rooms[room_key]
    if room_key == "salle5":
        spawn = target_room.spawn_points.get("spawn 2 joueur", target_room.spawn)
        if spawn:
            player1.x, player1.y = spawn
            player2.x, player2.y = spawn[0] + 50, spawn[1]
        else:
            player1.x, player1.y = 300, 300
            player2.x, player2.y = 350, 300
    else:
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
    enemy_list = salle4_enemies if current_room_key == "salle4" else salle5_enemies if current_room_key == "salle5" else []
    if not enemy_list:
        return
    for player in attacking_players:
        attack_rect = player.rect.inflate(34, 34)
        for enemy in enemy_list:
            if enemy.alive and attack_rect.colliderect(enemy.rect):
                enemy.take_damage(20)
                notification = "Ennemi touche !"
                notification_timer = 900
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
    salle4_enemies = [e for e in salle4_enemies if not e.death_anim_done]

def update_salle5_enemies():
    global salle5_enemies, salle5_wave1_spawned, salle5_wave2_spawned
    global salle5_wave3_spawned, salle5_wave4_spawned, salle5_bosses_spawned
    if current_room_key != "salle5":
        return

    r5 = rooms["salle5"]

    if not salle5_wave1_spawned:
        e1 = spawn_enemy_at("spawn ennemie 1", r5)
        e2 = spawn_enemy_at("spawn ennemie 2", r5)
        for e in [e1, e2]:
            if e:
                salle5_enemies.append(e)
        salle5_wave1_spawned = True

    if not salle5_wave2_spawned and not r5.wall_replace_active:
        e3 = spawn_enemy_at("spawn ennemie 3", r5)
        if e3:
            salle5_enemies.append(e3)
        salle5_wave2_spawned = True

    if not salle5_wave3_spawned and not r5.wall_replace3_active:
        for name in ("spawn ennemie 4", "spawn ennemie 5", "spawn ennemie 6", "spawn ennemie 7"):
            e = spawn_enemy_at(name, r5, scorpio=True)
            if e:
                salle5_enemies.append(e)
        salle5_wave3_spawned = True

    if not salle5_wave4_spawned and not r5.wall_replace4_active:
        e8 = spawn_enemy_at("spawn ennemie 8", r5, scorpio=True)
        if e8:
            salle5_enemies.append(e8)
        salle5_wave4_spawned = True

    if not salle5_bosses_spawned and not r5.wall_replace5_active:
        b1 = spawn_boss_at("spawn boss 1", r5)
        if b1:
            salle5_enemies.append(b1)
        sp2 = r5.spawn_points.get("spawn boss 2")
        if sp2:
            salle5_enemies.append(ScorpioBoss(sp2[0], sp2[1]))
        salle5_bosses_spawned = True

    active_players = [player1, player2]
    room_bounds = pygame.Rect(0, 0, SALLE5_W, SALLE5_H)
    for enemy in salle5_enemies:
        enemy.update(r5.collisions, active_players, room_bounds)
    salle5_enemies = [e for e in salle5_enemies if not e.death_anim_done]

def draw_enemies(surface, dt):
    # En mode client réseau (player2), on dessine les ennemis reçus du serveur
    if args.network == "client" and local_player_id == "player2":
        for e_data in remote_enemies:
            x, y = e_data["x"], e_data["y"]
            hp = e_data["hp"]
            max_hp = e_data["max_hp"]
            alive = e_data["alive"]
            state = e_data["state"]
            flip = e_data["flip"]

            # Dessine un sprite simplifié basé sur les données réseau
            color = (205, 55, 55) if "Scorpio" not in e_data["type"] else (180, 120, 30)
            if "Boss" in e_data["type"]:
                size = (96, 96)
            else:
                size = (64, 64)

            if alive and state != "death":
                rect = pygame.Rect(x, y, 30, 30)
                cx, cy = rect.centerx, rect.centery
                pygame.draw.rect(surface, color, (cx - size[0]//2, cy - size[1]//2, size[0], size[1]), border_radius=6)
                # Barre de vie
                bar_w = 30
                hp_w = int(bar_w * max(0, hp) / max(1, max_hp))
                pygame.draw.rect(surface, (70, 20, 20), (x, y - 7, bar_w, 4))
                pygame.draw.rect(surface, (230, 70, 70), (x, y - 7, hp_w, 4))
            # Projectiles
            for p in e_data.get("projectiles", []):
                pygame.draw.circle(surface, (255, 205, 70), (p["x"] + 5, p["y"] + 5), 5)
        return

    # Mode local / hôte : on dessine les vrais objets ennemis
    if current_room_key == "salle4":
        for e in salle4_enemies:
            e.draw(surface, dt)
    elif current_room_key == "salle5":
        for e in salle5_enemies:
            e.draw(surface, dt)

def teleport_via_portail(door_info, trigger):
    target = next((d for d in room.doors if d["name"] == door_info), None)
    if target:
        if trigger == "p1":
            player1.x, player1.y = target["rect"].x + 32, target["rect"].y
        else:
            player2.x, player2.y = target["rect"].x + 32, target["rect"].y

def restart_current_room():
    global notification, notification_timer
    reset_room_state(current_room_key)
    set_players_on_room_spawn(current_room_key)
    notification = "Un joueur est tombe ! Salle recommencee."
    notification_timer = 3000

def show_credits():
    credits_font = pygame.font.SysFont(None, 46)
    title_font = pygame.font.SysFont(None, 64)
    names = ["Nael", "Melissa", "Julia", "Hadrien", "Ghali"]
    lines = ["Merci d'avoir joue", "", "Equipe"] + names + ["", "Fin"]
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

salle5_surface = pygame.Surface((SALLE5_W, SALLE5_H))

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
            if event.key == pygame.K_F1:
                current_room_key = "salle4"
                room = rooms[current_room_key]
                set_players_on_room_spawn(current_room_key)
                reset_room_state(current_room_key)
            if event.key == pygame.K_F2:
                current_room_key = "salle5"
                room = rooms[current_room_key]
                set_players_on_room_spawn(current_room_key)
                reset_room_state(current_room_key)
            if args.network == "client" and event.key in NETWORK_ATTACK_KEYS:
                if local_player_id:
                    p = players[local_player_id]
                    if p.can_attack():
                        damage_enemies([p])
                        p.start_attack()
            elif args.network != "client":
                if event.key in PLAYER1_ATTACK_KEYS:
                    if player1.can_attack():
                        damage_enemies([player1])
                        player1.start_attack()
                if event.key in PLAYER2_ATTACK_KEYS:
                    if player2.can_attack():
                        damage_enemies([player2])
                        player2.start_attack()
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

        # Synchronisation de la salle : le client suit la salle de l'hôte
        net_room = state.get("room")
        if net_room and net_room != current_room_key and local_player_id == "player2":
            current_room_key = net_room
            room = rooms[current_room_key]
            set_players_on_room_spawn(current_room_key)
            reset_room_state(current_room_key)
            notification = None

        # Synchronisation des ennemis : le client reçoit et stocke
        if local_player_id == "player2":
            remote_enemies.clear()
            remote_enemies.extend(state.get("enemies", []))

        for net_event in state["events"]:
            if net_event.get("id", 0) <= last_network_event_id:
                continue
            last_network_event_id = net_event.get("id", last_network_event_id)
            event_player_id = net_event.get("player_id")
            if event_player_id != local_player_id and event_player_id in players:
                if net_event.get("type") == "interact":
                    activate_local_leviers(players[event_player_id])

        # L'hôte envoie aussi l'état des ennemis à chaque frame
        enemies_data = _serialize_enemies() if local_player_id == "player1" else None
        network_client.send_player_state(
            players[local_player_id].to_network_state(),
            network_event,
            enemies=enemies_data,
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

    door_status, door_info, door_trigger = room.check_doors(p1_rect, p2_rect)
    room.check_plaques(p1_rect, p2_rect)

    # Seul l'hôte (ou le mode local) simule les ennemis
    if args.network != "client" or local_player_id == "player1":
        update_salle4_enemies()
        update_salle5_enemies()

    if (args.network != "client" or local_player_id == "player1") and (
        current_room_key == "salle5"
        and salle5_bosses_spawned
        and len(salle5_enemies) == 0
    ):
        show_credits()
        running = False

    room_restarted = player1.hp <= 0 or player2.hp <= 0
    if room_restarted:
        restart_current_room()
        p1_rect = player_rect(player1)
        p2_rect = player_rect(player2)

    # Seul l'hôte (ou le mode local) décide du changement de salle
    is_host_or_local = args.network != "client" or local_player_id == "player1"

    if not room_restarted and door_status == "portail" and door_info:
        teleport_via_portail(door_info, door_trigger)
    elif is_host_or_local and not room_restarted and door_status == "both" and door_info:
        both_door_frames += 1
        # En réseau on attend 2 frames consécutives pour éviter les faux positifs dus au délai réseau
        required_frames = 2 if args.network == "client" else 1
        if both_door_frames >= required_frames:
            both_door_frames = 0
            current_room_key = door_info
            room = rooms[current_room_key]
            set_players_on_room_spawn(current_room_key)
            reset_room_state(current_room_key)
            notification = None
            if args.network == "client" and local_player_id and network_client:
                network_client.send_player_state(
                    players[local_player_id].to_network_state(),
                    room=current_room_key,
                )
    elif is_host_or_local and not room_restarted and door_status == "one":
        both_door_frames = 0
        notification = "Les deux joueurs doivent atteindre la porte de sortie !"
        notification_timer = 3000
    else:
        both_door_frames = 0

    screen.fill((0, 0, 0))

    if current_room_key == "salle5":
        salle5_surface.fill((0, 0, 0))
        room.draw(salle5_surface, dt, p1_rect, p2_rect)
        draw_enemies(salle5_surface, dt)
        player1.draw(salle5_surface)
        player2.draw(salle5_surface)
        scaled = pygame.transform.scale(salle5_surface, (SCREEN_W, SCREEN_H))
        screen.blit(scaled, (0, 0))
    else:
        room.draw(screen, dt, p1_rect, p2_rect)
        draw_enemies(screen, dt)
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

    if current_room_key == "salle1" and controls_timer > 0:
        controls_timer -= dt
        lines = ["ZQSD : Se deplacer", "E : Interagir", "F : Attaquer"]
        tip_font = pygame.font.SysFont(None, 28)
        pad = 10
        line_h = tip_font.get_linesize()
        box_w = 220
        box_h = len(lines) * line_h + pad * 2
        box_x = 10
        box_y = SCREEN_H - box_h - 10
        tip_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        tip_surf.fill((20, 20, 20, 160))
        screen.blit(tip_surf, (box_x, box_y))
        for i, line in enumerate(lines):
            txt = tip_font.render(line, True, (255, 255, 255))
            screen.blit(txt, (box_x + pad, box_y + pad + i * line_h))

    pygame.display.flip()

if network_client:
    network_client.close()
if local_server:
    local_server.stop()
pygame.quit()