import pygame
from settings import *
from player import Player
from enemy import Enemy

pygame.init()

# Plein écran
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH  = screen.get_width()
SCREEN_HEIGHT = screen.get_height()
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Calcul dynamique des tiles pour remplir l'écran
TILE_SIZE  = 48  # plus grand pour remplir l'écran
GRID_COLS  = SCREEN_WIDTH  // TILE_SIZE
GRID_ROWS  = SCREEN_HEIGHT // TILE_SIZE

print(f"Résolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
print(f"Grille: {GRID_COLS}x{GRID_ROWS} tiles")

def make_grid(cols, rows):
    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            # Bordures
            if x == 0 or x == cols-1 or y == 0 or y == rows-1:
                row.append(1)
            # Obstacles en croix espacés
            elif (x % 7 == 3 and 2 <= y <= rows-3 and y % 4 != 0):
                row.append(1)
            elif (x % 9 == 6 and 2 <= y <= rows-3 and y % 3 != 0):
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
    return grid

collision_grid = make_grid(GRID_COLS, GRID_ROWS)

# Porte à droite au milieu
DOOR_TILE = (GRID_COLS - 2, GRID_ROWS // 2)
collision_grid[DOOR_TILE[1]][DOOR_TILE[0]] = 0

# Position de la porte (tile x=23, y=7)
DOOR_TILE = (23, 7)
door_rect = pygame.Rect(
    DOOR_TILE[0] * TILE_SIZE,
    DOOR_TILE[1] * TILE_SIZE,
    TILE_SIZE, TILE_SIZE
)

def draw_grid(surface):
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if collision_grid[y][x] == 1:
                pygame.draw.rect(surface, GREY, rect)
            else:
                pygame.draw.rect(surface, (40, 40, 40), rect)
            pygame.draw.rect(surface, (60, 60, 60), rect, 1)
    # Porte
    door_rect = pygame.Rect(DOOR_TILE[0]*TILE_SIZE, DOOR_TILE[1]*TILE_SIZE, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(surface, YELLOW, door_rect)
    font = pygame.font.SysFont(None, 28)
    txt = font.render("EXIT", True, BLACK)
    surface.blit(txt, (door_rect.x + 4, door_rect.y + TILE_SIZE//2 - 8))


def check_door(player, reached_set, player_id):
    tx = player.rect.centerx // TILE_SIZE
    ty = player.rect.centery // TILE_SIZE
    if (tx, ty) == DOOR_TILE:
        reached_set.add(player_id)

def draw_ui(surface, p1_done, p2_done):
    font = pygame.font.SysFont(None, 28)
    p1_txt = font.render(f"P1: {'✓ Sorti !' if p1_done else 'En jeu'}", True, BLUE)
    p2_txt = font.render(f"P2: {'✓ Sorti !' if p2_done else 'En jeu'}", True, GREEN)
    surface.blit(p1_txt, (10, 10))
    surface.blit(p2_txt, (10, 35))

controls_p1 = {
    'up': pygame.K_z, 'down': pygame.K_s,
    'left': pygame.K_q, 'right': pygame.K_d,
}
controls_p2 = {
    'up': pygame.K_UP, 'down': pygame.K_DOWN,
    'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
}

player1 = Player(2, GRID_ROWS//2 - 1, BLUE,  controls_p1, TILE_SIZE)
player2 = Player(2, GRID_ROWS//2 + 1, GREEN, controls_p2, TILE_SIZE)

mid = GRID_ROWS // 2
patrol1 = [(6, mid-2), (GRID_COLS//2, mid-2), (GRID_COLS//2, mid+2), (6, mid+2)]
patrol2 = [(GRID_COLS//2+2, mid-2), (GRID_COLS-4, mid-2),
           (GRID_COLS-4, mid+2), (GRID_COLS//2+2, mid+2)]

enemy1 = Enemy(6, mid, patrol1, enemy_type="melee",  tile_size=TILE_SIZE)
enemy2 = Enemy(GRID_COLS//2+2, mid, patrol2, enemy_type="archer", tile_size=TILE_SIZE)

all_sprites = pygame.sprite.Group(player1, player2, enemy1, enemy2)
reached = set()
game_over = False
font_big = pygame.font.SysFont(None, 64)

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Restart avec R
            if event.key == pygame.K_r and game_over:
                player1.rect.x = 2 * TILE_SIZE
                player1.rect.y = 6 * TILE_SIZE
                player2.rect.x = 2 * TILE_SIZE
                player2.rect.y = 8 * TILE_SIZE
                reached.clear()
                game_over = False

    if not game_over:
        player1.update(collision_grid)
        player2.update(collision_grid)
        enemy1.update(collision_grid, [player1, player2])
        enemy2.update(collision_grid, [player1, player2])

        check_door(player1, reached, 1)
        check_door(player2, reached, 2)

        if 1 in reached and 2 in reached:
            game_over = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and game_over:
                # reset
                player1.rect.x = 2 * TILE_SIZE
                player1.rect.y = (GRID_ROWS//2 - 1) * TILE_SIZE
                player2.rect.x = 2 * TILE_SIZE
                player2.rect.y = (GRID_ROWS//2 + 1) * TILE_SIZE
                reached.clear()
                game_over = False
    # Affichage
    draw_grid(screen)
    for sprite in all_sprites:
        for proj in enemy2.projectiles:
            screen.blit(proj.image, proj.rect)
        screen.blit(sprite.image, sprite.rect)

    def draw_hp_bar(surface, enemy, cam_x=0, cam_y=0):
        bar_w = TILE_SIZE - 4
        bar_h = 5
        x = enemy.rect.x - cam_x
        y = enemy.rect.y - cam_y - 8
        fill = int(bar_w * enemy.hp / enemy.hp_max)
        color = GREEN if enemy.hp > 50 else (YELLOW if enemy.hp > 25 else RED)
        pygame.draw.rect(screen, (80, 0, 0), (x, y, bar_w, bar_h))
        pygame.draw.rect(screen, color,      (x, y, fill,  bar_h))

    draw_hp_bar(screen, enemy1)
    draw_hp_bar(screen, enemy2)
    draw_ui(screen, 1 in reached, 2 in reached)

    if game_over:
        txt = font_big.render("VICTOIRE ! (R pour rejouer)", True, YELLOW)
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2,
                          SCREEN_HEIGHT // 2 - txt.get_height() // 2))
    
    font_ui = pygame.font.SysFont(None, 32)
    exit_txt = font_ui.render("[ ESC ] Quitter", True, (200, 200, 200))
    screen.blit(exit_txt, (SCREEN_WIDTH - exit_txt.get_width() - 15, 10))

    pygame.display.flip()

pygame.quit()