import pygame
import pytmx
import sys
import os

# ─────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
FPS           = 60
TILE_SIZE     = 32

MAP_PATH         = "IA/MAP-FINAL-HORIZONTAL.tmx"
COLLISION_LAYERS = ["wall", "trou lave"]
BG_COLOR         = (20, 20, 30)


# ─────────────────────────────────────────
#  JOUEUR
# ─────────────────────────────────────────
class Player:
    SPEED = 3  # pixels par frame (dans l'espace carte, avant scale)

    def __init__(self, x: int, y: int):
        self.rect  = pygame.Rect(x, y, TILE_SIZE - 4, TILE_SIZE - 4)
        self.color = (230, 180, 80)

    def move(self, dx: int, dy: int, collision_rects: list):
        self.rect.x += dx
        for wall in collision_rects:
            if self.rect.colliderect(wall):
                if dx > 0: self.rect.right = wall.left
                else:       self.rect.left  = wall.right

        self.rect.y += dy
        for wall in collision_rects:
            if self.rect.colliderect(wall):
                if dy > 0: self.rect.bottom = wall.top
                else:       self.rect.top    = wall.bottom

    def handle_input(self, keys, collision_rects: list):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_q]: dx -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.SPEED
        if keys[pygame.K_UP]    or keys[pygame.K_z]: dy -= self.SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += self.SPEED
        self.move(dx, dy, collision_rects)

    def draw(self, surface: pygame.Surface, scale_x: float, scale_y: float,
             offset_x: int = 0, offset_y: int = 0):
        draw_rect = pygame.Rect(
            int(self.rect.x * scale_x) + offset_x,
            int(self.rect.y * scale_y) + offset_y,
            max(2, int(self.rect.w * scale_x)),
            max(2, int(self.rect.h * scale_y)),
        )
        pygame.draw.rect(surface, self.color, draw_rect)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, 1)


# ─────────────────────────────────────────
#  CHARGEMENT CARTE + COLLISIONS
# ─────────────────────────────────────────
def load_map(path: str):
    return pytmx.util_pygame.load_pygame(path)


def build_collision_rects(tiled_map) -> list:
    rects = []
    for layer in tiled_map.layers:
        if hasattr(layer, 'name') and layer.name in COLLISION_LAYERS:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    if gid:
                        rects.append(pygame.Rect(
                            x * tiled_map.tilewidth,
                            y * tiled_map.tileheight,
                            tiled_map.tilewidth,
                            tiled_map.tileheight,
                        ))
    return rects


# ─────────────────────────────────────────
#  RENDU CARTE SUR SURFACE INTERMÉDIAIRE
# ─────────────────────────────────────────
def draw_map_to_surface(tiled_map) -> pygame.Surface:
    """
    Dessine toute la carte une seule fois sur une surface pleine taille.
    Cette surface est ensuite scalée à la taille de la fenêtre.
    """
    tw = tiled_map.tilewidth
    th = tiled_map.tileheight
    w  = tiled_map.width  * tw
    h  = tiled_map.height * th

    surf = pygame.Surface((w, h))
    surf.fill(BG_COLOR)

    for layer in tiled_map.visible_layers:
        if not isinstance(layer, pytmx.TiledTileLayer):
            continue
        for x, y, image in layer.tiles():
            if image:
                surf.blit(image, (x * tw, y * th))

    return surf


# ─────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Salle Test – Donjon")
    clock = pygame.time.Clock()

    # ── Chargement ───────────────────────────────────────────────────────────
    if not os.path.exists(MAP_PATH):
        print(f"[ERREUR] Carte introuvable : {MAP_PATH}")
        sys.exit(1)

    print("Chargement de la carte…")
    tiled_map = load_map(MAP_PATH)
    print("Carte chargée !")

    map_pixel_w = tiled_map.width  * tiled_map.tilewidth   # 12800 px
    map_pixel_h = tiled_map.height * tiled_map.tileheight  #  2560 px

    # On garde le ratio original de la carte (pas de déformation).
    # On prend le facteur le plus petit pour que tout rentre dans la fenêtre.
    scale   = min(WINDOW_WIDTH / map_pixel_w, WINDOW_HEIGHT / map_pixel_h)
    scale_x = scale
    scale_y = scale

    scaled_w = int(map_pixel_w * scale)
    scaled_h = int(map_pixel_h * scale)

    # Offset pour centrer la carte si elle ne remplit pas toute la fenêtre
    offset_x = (WINDOW_WIDTH  - scaled_w) // 2
    offset_y = (WINDOW_HEIGHT - scaled_h) // 2

    # ── Surface carte rendue une seule fois puis scalée ───────────────────────
    print("Rendu de la carte (peut prendre quelques secondes)…")
    map_surface = draw_map_to_surface(tiled_map)
    map_scaled  = pygame.transform.scale(map_surface, (scaled_w, scaled_h))
    print("Prêt !")

    # ── Collisions (dans l'espace carte, pas écran) ───────────────────────────
    collision_rects = build_collision_rects(tiled_map)
    print(f"  → {len(collision_rects)} tuiles solides.")

    # ── Joueur (coordonnées dans l'espace carte) ──────────────────────────────
    player = Player(map_pixel_w // 2, map_pixel_h // 2)

    font = pygame.font.SysFont("monospace", 14)

    # ─────────────────────────────────────────────────────────────────────────
    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.handle_input(keys, collision_rects)
        # Caméra horizontale uniquement
        camera_x = player.rect.centerx * scale_x - WINDOW_WIDTH // 2
        # Limites (ne pas sortir de la map)
        camera_x = max(0, min(camera_x, scaled_w - WINDOW_WIDTH))

        # ── Rendu ─────────────────────────────────────────────────────────────
        screen.fill(BG_COLOR)
        screen.blit(map_scaled, (-camera_x + offset_x, offset_y))  # carte centrée
        player.draw(screen, scale_x, scale_y, offset_x - camera_x, offset_y)

        hud = font.render(
            f"Pos: ({player.rect.x}, {player.rect.y})  |  ZQSD / Flèches  |  ESC quitter",
            True, (220, 220, 220)
        )
        screen.blit(hud, (8, 8))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()