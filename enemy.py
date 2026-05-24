import math
import pygame
 
 
FRAME_SIZE = 48
 
_sheet_cache = {}
 
def _load(path):
    if path not in _sheet_cache:
        _sheet_cache[path] = pygame.image.load(path).convert_alpha()
    return _sheet_cache[path]
 
def _get_frame(sheet, index):
    return sheet.subsurface((index * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE))
 
 
class Projectile:
    def __init__(self, x, y, target_x, target_y):
        self.rect = pygame.Rect(x - 5, y - 5, 10, 10)
        self.speed = 4.5
        self.life = 120
        dx = target_x - x
        dy = target_y - y
        dist = max(1, math.hypot(dx, dy))
        self.vx = self.speed * dx / dist
        self.vy = self.speed * dy / dist
 
    def update(self, collisions, players, bounds=None):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.life -= 1
 
        if self.life <= 0 or any(self.rect.colliderect(wall) for wall in collisions):
            return False
        if bounds and not bounds.colliderect(self.rect):
            return False
 
        for player in players:
            if self.rect.colliderect(player.rect):
                player.take_hit(self.rect.centerx, self.rect.centery, 12, collisions, bounds)
                return False
        return True
 
    def draw(self, surface):
        pygame.draw.circle(surface, (255, 205, 70), self.rect.center, 5)
 
 
class RoomEnemy:
    def __init__(
            self,
            x,
            y,
            target_player=None,
            hp=45,
            speed=1.4,
            color=(205, 55, 55),
    ):
        self.rect = pygame.Rect(int(x), int(y), 30, 30)
        self.spawn = pygame.Vector2(self.rect.center)
        self.target_player = target_player
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.color = color
        self.flip = False
        self.attack_cooldown = 0
        self.alive = True
 
        self.sheet_idle = _load("assets/Mummy_idle.png")
        self.sheet_walk = _load("assets/Mummy_walk.png")
        self.sheet_attack = _load("assets/Mummy_attack.png")
        self.sheet_hurt = _load("assets/Mummy_hurt.png")
        self.sheet_death = _load("assets/Mummy_death.png")
 
        self.anim_timer = 0
        self.anim_frame = 0
        self.anim_sheet = self.sheet_idle
        self.anim_frames = 4
        self.anim_speed = 120
        self.state = "idle"
        self.draw_size = (64, 64)
 
    def _set_anim(self, state):
        if self.state == state:
            return
        self.state = state
        self.anim_frame = 0
        self.anim_timer = 0
        if state == "idle":
            self.anim_sheet = self.sheet_idle
            self.anim_frames = 4
            self.anim_speed = 150
        elif state == "walk":
            self.anim_sheet = self.sheet_walk
            self.anim_frames = 6
            self.anim_speed = 100
        elif state == "attack":
            self.anim_sheet = self.sheet_attack
            self.anim_frames = 6
            self.anim_speed = 80
        elif state == "hurt":
            self.anim_sheet = self.sheet_hurt
            self.anim_frames = 2
            self.anim_speed = 80
        elif state == "death":
            self.anim_sheet = self.sheet_death
            self.anim_frames = 6
            self.anim_speed = 120
 
    def _advance_anim(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            if self.state == "death":
                if self.anim_frame < self.anim_frames - 1:
                    self.anim_frame += 1
            else:
                self.anim_frame = (self.anim_frame + 1) % self.anim_frames
 
    def update(self, collisions, players, bounds=None):
        if not self.alive:
            return
 
        if self.state == "death":
            return
 
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1