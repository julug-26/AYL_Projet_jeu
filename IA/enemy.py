import pygame
from settings import *
from pathfinding import astar

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 200, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        dx = target_x - x
        dy = target_y - y
        dist = max(1, (dx**2 + dy**2) ** 0.5)
        self.vx = self.speed * dx / dist
        self.vy = self.speed * dy / dist
        self.lifetime = 120  # frames

    def update(self, collision_grid):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.lifetime -= 1

        tx = self.rect.centerx // TILE_SIZE
        ty = self.rect.centery // TILE_SIZE
        if ty < 0 or ty >= len(collision_grid): self.kill(); return
        if tx < 0 or tx >= len(collision_grid[0]): self.kill(); return
        if collision_grid[ty][tx] == 1:
            self.kill()
        if self.lifetime <= 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_points, enemy_type="melee", tile_size=32):
        super().__init__()
        self.tile_size = tile_size
        self.enemy_type = enemy_type  # "melee" ou "archer"

        # Couleurs selon type
        if enemy_type == "melee":
            self.base_color = (220, 50, 50)    # Rouge
        else:
            self.base_color = (150, 50, 220)   # Violet

        self.image = pygame.Surface((self.tile_size - 4, self.tile_size - 4))
        self.image.fill(self.base_color)
        self.rect = self.image.get_rect()
        self.rect.x = x * self.tile_size
        self.rect.y = y * self.tile_size
        self.origin = (x * self.tile_size, y * self.tile_size)

        # Stats
        self.hp          = 100
        self.hp_max      = 100
        self.flee_threshold = 30  # fuit sous 30% HP

        # Vitesses
        self.patrol_speed = 1
        self.chase_speed  = 2
        self.flee_speed   = 3

        # Combat
        self.detection_range  = 12   # tiles (augmenté)
        self.attack_range     = 1.5  # tiles (mêlée)
        self.archer_min_range = 3    # tiles (archer recule si trop proche)
        self.archer_max_range = 10  # tiles (archer tire jusqu'ici)
        self.attack_cooldown  = 0
        self.attack_delay     = 60

        # Patrouille
        self.patrol_points = patrol_points
        self.patrol_index  = 0
        self.patrol_pause  = 0    # pause entre points
        self.patrol_speed = 1
        self.chase_speed  = 3  # augmenté de 2 à 3
        self.flee_speed   = 4  # augmenté de 3 à 4

        # Pathfinding
        self.path        = []
        self.path_timer  = 0
        self.path_delay  = 30

        # État
        self.state = "patrol"

        # Projectiles (archer)
        self.projectiles = pygame.sprite.Group()

        # Origine (pour repli)
        self.origin = (x * TILE_SIZE, y * TILE_SIZE)

    def get_tile_pos(self):
        return (self.rect.centerx // self.tile_size,
                self.rect.centery // self.tile_size)

    def _dist_tiles(self, tile_pos):
        my = self.get_tile_pos()
        return abs(my[0] - tile_pos[0]) + abs(my[1] - tile_pos[1])

    def _nearest_player(self, players):
        return min(players, key=lambda p: self._dist_tiles(p.get_tile_pos()))

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def _move_towards_path(self, speed):
        if not self.path:
            return
        next_tile = self.path[0]
        target_x  = next_tile[0] * self.tile_size + self.tile_size // 2
        target_y  = next_tile[1] * self.tile_size + self.tile_size // 2
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = max(1, (dx**2 + dy**2) ** 0.5)
        self.rect.x += int(speed * dx / dist)
        self.rect.y += int(speed * dy / dist)
        if abs(self.rect.centerx - target_x) < speed + 1 and \
           abs(self.rect.centery - target_y) < speed + 1:
            self.path.pop(0)

    def _recalc_path(self, collision_grid, goal):
        self.path_timer = 0
        self.path = astar(collision_grid, self.get_tile_pos(), goal)

    def _draw_hp_bar(self):
        """Redessine le rectangle proprement avec la couleur de base."""
        # Couleur selon état
        if self.state == "patrol":
            color = self.base_color
        elif self.state == "chase":
            color = (255, 80, 80) if self.enemy_type == "melee" else (200, 80, 255)
        else:  # flee
            color = (255, 165, 0)
        self.image.fill(color)

    def update(self, collision_grid, players):
        nearest  = self._nearest_player(players)
        dist     = self._dist_tiles(nearest.get_tile_pos())

        # --- Décision d'état (priorités de la charte) ---
        hp_pct = self.hp / self.hp_max * 100
        if hp_pct <= self.flee_threshold:
            self.state = "flee"
        elif dist <= self.detection_range:
            self.state = "chase"
        else:
            self.state = "patrol"

        # Cooldown attaque
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # --- Comportement par état ---
        self.path_timer += 1

        if self.state == "patrol":
            self.image.fill(self.base_color)
            if self.patrol_pause > 0:
                self.patrol_pause -= 1
                return
            target = self.patrol_points[self.patrol_index]
            if self.path_timer >= self.path_delay or not self.path:
                self._recalc_path(collision_grid, target)
            self._move_towards_path(self.patrol_speed)
            # Arrivé au point de patrouille
            if self.get_tile_pos() == target:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                self.patrol_pause = 40  # pause naturelle

        elif self.state == "chase":
            # Couleur plus vive en chasse
            self.image.fill((255, 80, 80) if self.enemy_type == "melee" else (200, 80, 255))

            if self.enemy_type == "melee":
                # Corps à corps : fonce sur le joueur
                if self.path_timer >= self.path_delay or not self.path:
                    self._recalc_path(collision_grid, nearest.get_tile_pos())
                self._move_towards_path(self.chase_speed)

                # Attaque au contact
                if dist <= self.attack_range and self.attack_cooldown == 0:
                    nearest.take_hit(self.rect.centerx, self.rect.centery)
                    self.attack_cooldown = self.attack_delay

            else:  # archer
                # Garde une distance optimale
                if dist < self.archer_min_range:
                    # Trop proche : recule
                    goal_x = self.rect.centerx + (self.rect.centerx - nearest.rect.centerx)
                    goal_y = self.rect.centery + (self.rect.centery - nearest.rect.centery)
                    goal_tile = (max(1, min(goal_x // self.tile_size, len(collision_grid[0])-2)),
                                 max(1, min(goal_y // self.tile_size, len(collision_grid)-2)))
                    if self.path_timer >= self.path_delay or not self.path:
                        self._recalc_path(collision_grid, goal_tile)
                    self._move_towards_path(self.chase_speed)

                elif dist <= self.archer_max_range:
                    # Dans la portée de tir : tire !
                    self.path = []
                    if self.attack_cooldown == 0:
                        proj = Projectile(
                            self.rect.centerx, self.rect.centery,
                            nearest.rect.centerx, nearest.rect.centery
                        )
                        self.projectiles.add(proj)
                        self.attack_cooldown = self.attack_delay
                else:
                    # Trop loin : se rapproche
                    if self.path_timer >= self.path_delay or not self.path:
                        self._recalc_path(collision_grid, nearest.get_tile_pos())
                    self._move_towards_path(self.chase_speed)

        elif self.state == "flee":
            self.image.fill((255, 165, 0))  # Orange = fuite
            # Fuit vers son point d'origine
            origin_tile = (self.origin[0] // self.tile_size, self.origin[1] // self.tile_size)
            if self.path_timer >= self.path_delay or not self.path:
                self._recalc_path(collision_grid, origin_tile)
            self._move_towards_path(self.flee_speed)

        # Update projectileselse:  # archer
        else:
            if dist < self.archer_min_range:
            # Trop proche : recule vers son point de patrouille le plus proche
                target = self.patrol_points[self.patrol_index]
                if self.path_timer >= self.path_delay or not self.path:
                    self._recalc_path(collision_grid, target)
                self._move_towards_path(self.chase_speed)

            elif dist <= self.archer_max_range:
            # Dans la portée de tir : s'arrête et tire
                self.path = []
                if self.attack_cooldown == 0:
                    proj = Projectile(
                    self.rect.centerx, self.rect.centery,
                    nearest.rect.centerx, nearest.rect.centery
                    )
                    self.projectiles.add(proj)
                    self.attack_cooldown = self.attack_delay

            else:
        # Trop loin : se rapproche jusqu'à portée de tir
                if self.path_timer >= self.path_delay or not self.path:
                    self._recalc_path(collision_grid, nearest.get_tile_pos())
                self._move_towards_path(self.chase_speed)
        
        self.projectiles.update(collision_grid)

        # Vérifie si projectile touche un joueur
        for proj in self.projectiles:
            for player in players:
                if proj.rect.colliderect(player.rect):
                    player.take_hit(proj.rect.centerx, proj.rect.centery)
                    proj.kill()

        # Barre de vie
        self._draw_hp_bar()