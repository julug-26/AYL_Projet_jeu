import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, color, controls, tile_size=32):
        super().__init__()
        self.tile_size = tile_size
        self.base_color = color
        self.image = pygame.Surface((tile_size - 4, tile_size - 4))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x * tile_size
        self.rect.y = y * tile_size
        self.speed = 3
        self.controls = controls
        self.knockback_vx    = 0
        self.knockback_vy    = 0
        self.knockback_timer = 0
        self.hit_timer    = 0
        self.hit_duration = 40

        self.controls = controls

        # Knockback
        self.knockback_vx    = 0
        self.knockback_vy    = 0
        self.knockback_timer = 0

        # Flash rouge
        self.hit_timer    = 0
        self.hit_duration = 40

    def take_hit(self, from_x, from_y):
        if self.hit_timer > 0:
            return
        self.hit_timer = self.hit_duration

        # Knockback léger
        dx = self.rect.centerx - from_x
        dy = self.rect.centery - from_y
        dist = max(1, (dx**2 + dy**2) ** 0.5)
        self.knockback_vx    = int(3 * dx / dist)  # réduit de 8 à 3
        self.knockback_vy    = int(3 * dy / dist)
        self.knockback_timer = 6                    # réduit de 10 à 6

    def update(self, collision_grid):
        # Flash rouge simple : rouge pendant les 15 premières frames, sinon couleur normale
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer > self.hit_duration - 15:
                self.image.fill((255, 60, 60))  # rouge vif
            else:
                self.image.fill(self.base_color)
        else:
            self.image.fill(self.base_color)

        # Knockback
        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.rect.x += self.knockback_vx
            if self._check_collision(collision_grid):
                self.rect.x -= self.knockback_vx
            self.rect.y += self.knockback_vy
            if self._check_collision(collision_grid):
                self.rect.y -= self.knockback_vy
            return

        # Déplacement normal
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[self.controls['up']]:    dy = -self.speed
        if keys[self.controls['down']]:  dy =  self.speed
        if keys[self.controls['left']]:  dx = -self.speed
        if keys[self.controls['right']]: dx =  self.speed

        self.rect.x += dx
        if self._check_collision(collision_grid):
            self.rect.x -= dx

        self.rect.y += dy
        if self._check_collision(collision_grid):
            self.rect.y -= dy

    def _check_collision(self, collision_grid):
        corners = [
            (self.rect.left,    self.rect.top),
            (self.rect.right-1, self.rect.top),
            (self.rect.left,    self.rect.bottom-1),
            (self.rect.right-1, self.rect.bottom-1),
        ]
        for cx, cy in corners:
            tx = cx // self.tile_size
            ty = cy // self.tile_size
            if ty < 0 or ty >= len(collision_grid): continue
            if tx < 0 or tx >= len(collision_grid[0]): continue
            if collision_grid[ty][tx] == 1:
                return True
        return False

    def get_tile_pos(self):
        return (self.rect.centerx // self.tile_size,
            self.rect.centery // self.tile_size)