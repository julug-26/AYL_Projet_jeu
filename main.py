import pygame
from room import Room
from player import Player
import network

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

# Choix du joueur au lancement
player_id = input("Tu es joueur 1 (fleches) ou 2 (zqsd) ? Tape 1 ou 2 : ")
if player_id == "1":
    my_player = player1
    my_key = "player1"
else:
    my_player = player2
    my_key = "player2"

# Connexion au serveur
network.connect_to_server('127.0.0.1')  # Change IP si LAN

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not network.sock or network.sock.fileno() < 0:
        print("Déconnecté du serveur")
        break

    # Envoie inputs du joueur local au serveur
    try:
        inputs = my_player.get_input()
        inputs["player_id"] = my_key  # Dit au serveur qui envoie
        network.send_inputs(inputs)
    except Exception as e:
        print(f"Erreur réseau: {e}")
        break

    # Applique état serveur aux deux joueurs
    state = network.game_state
    if "player1" in state:
        player1.apply_state(state["player1"])
    if "player2" in state:
        player2.apply_state(state["player2"])

    # Items
    p1_rect = pygame.Rect(player1.x, player1.y, 48, 64)
    p2_rect = pygame.Rect(player2.x, player2.y, 48, 64)
    for rect in [p1_rect, p2_rect]:
        collected = room.check_items(rect)
        for item in collected:
            print(f"Ramassé : {item}")

    # Rendu
    screen.fill((0, 0, 0))
    room.draw(screen)
    player1.draw(screen)
    player2.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)

try:
    network.sock.close()
except:
    pass
pygame.quit()
