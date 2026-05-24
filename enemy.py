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
 
        target = self._target(players)
        moving = False
        if target:
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            if dx != 0:
                self.flip = dx < 0
            dist = math.hypot(dx, dy)
            if dist > 2:
                self._move_towards(target.rect.center, collisions)
                moving = True
            if self.rect.colliderect(target.rect) and self.attack_cooldown == 0:
                target.take_hit(self.rect.centerx, self.rect.centery, 8, collisions, bounds)
                self.attack_cooldown = 55
                self._set_anim("attack")
                return
 
        if self.state == "attack" and self.anim_frame >= self.anim_frames - 1:
            self._set_anim("idle")
 
        if self.state not in ("attack", "hurt"):
            self._set_anim("walk" if moving else "idle")
 
    def _target(self, players):
        if self.target_player is not None:
            return players[self.target_player]
        return min(players, key=lambda player: self._distance_to(player.rect.center))
 
    def _move_towards(self, target, collisions):
        dx = target[0] - self.rect.centerx
        dy = target[1] - self.rect.centery
        dist = max(1, math.hypot(dx, dy))
        move_x = self._step_towards(dx, dist)
        move_y = self._step_towards(dy, dist)
 
        old = self.rect.copy()
        self.rect.x += move_x
        if move_x < 0:
            self.flip = True
        elif move_x > 0:
            self.flip = False
        if any(self.rect.colliderect(wall) for wall in collisions):
            self.rect.x = old.x
        self.rect.y += move_y
        if any(self.rect.colliderect(wall) for wall in collisions):
            self.rect.y = old.y

    def _step_towards(self, delta, dist):
        if delta == 0:
            return 0
        step = int(round(self.speed * delta / dist))
        if step == 0:
            return 1 if delta > 0 else -1
        return step
 
    def _distance_to(self, point):
        return abs(self.rect.centerx - point[0]) + abs(self.rect.centery - point[1])
 
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            self._set_anim("death")
        else:
            self._set_anim("hurt")
 
    def draw(self, surface, dt=16):
        self._advance_anim(dt)
        frame = _get_frame(self.anim_sheet, self.anim_frame)
        scaled = pygame.transform.scale(frame, self.draw_size)
        if self.flip:
            scaled = pygame.transform.flip(scaled, True, False)
        cx, cy = self.rect.center
        surface.blit(scaled, (cx - self.draw_size[0] // 2, cy - self.draw_size[1] // 2))
        if self.alive:
            self._draw_hp(surface)
 
    def _draw_hp(self, surface):
        hp_w = int(self.rect.width * max(0, self.hp) / self.max_hp)
        pygame.draw.rect(surface, (70, 20, 20), (self.rect.x, self.rect.y - 7, self.rect.width, 4))
        pygame.draw.rect(surface, (230, 70, 70), (self.rect.x, self.rect.y - 7, hp_w, 4))
 
 
class BossEnemy(RoomEnemy):
    def __init__(self, x, y):
        super().__init__(
            x,
            y,
            target_player=None,
            hp=140,
            speed=1.2,
            color=(130, 60, 210),
        )
        self.projectiles = []
        self.shoot_cooldown = 80
        self.draw_size = (96, 96)
 
    def update(self, collisions, players, bounds=None):
        super().update(collisions, players, bounds)
        if not self.alive or self.state == "death":
            return
 
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            target = self._target(players)
            self.projectiles.append(Projectile(
                self.rect.centerx,
                self.rect.centery,
                target.rect.centerx,
                target.rect.centery,
            ))
            self._set_anim("attack")
            self.shoot_cooldown = 90
 
        self.projectiles = [
            p for p in self.projectiles
            if p.update(collisions, players, bounds)
        ]
 
    def draw(self, surface, dt=16):
        super().draw(surface, dt)
        for p in self.projectiles:
            p.draw(surface)
