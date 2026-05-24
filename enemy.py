import math
import pygame


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
            sprite_path="assets/tilesets/attaque_vert.webp",
    ):
        self.rect = pygame.Rect(int(x), int(y), 30, 30)
        self.spawn = pygame.Vector2(self.rect.center)
        self.target_player = target_player
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.color = color
        self.sprite = self._load_sprite(sprite_path)
        self.flip = False
        self.attack_cooldown = 0
        self.alive = True

    def _load_sprite(self, sprite_path):
        try:
            image = pygame.image.load(sprite_path).convert_alpha()
            return pygame.transform.smoothscale(image, (44, 44))
        except pygame.error:
            return None

    def update(self, collisions, players, bounds=None):
        if not self.alive:
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        target = self._target(players)
        if target:
            self._move_towards(target.rect.center, collisions)
            if self.rect.colliderect(target.rect) and self.attack_cooldown == 0:
                target.take_hit(self.rect.centerx, self.rect.centery, 8, collisions, bounds)
                self.attack_cooldown = 55

    def _target(self, players):
        if self.target_player is not None:
            return players[self.target_player]
        return min(players, key=lambda player: self._distance_to(player.rect.center))

    def _move_towards(self, target, collisions):
        dx = target[0] - self.rect.centerx
        dy = target[1] - self.rect.centery
        dist = max(1, math.hypot(dx, dy))
        move_x = int(self.speed * dx / dist)
        move_y = int(self.speed * dy / dist)

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

    def _distance_to(self, point):
        return abs(self.rect.centerx - point[0]) + abs(self.rect.centery - point[1])

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        if self.sprite:
            sprite = pygame.transform.flip(self.sprite, self.flip, False)
            surface.blit(sprite, sprite.get_rect(center=self.rect.center))
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=6)
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
            sprite_path="assets/tilesets/archer_rouge.webp",
        )
        self.projectiles = []
        self.shoot_cooldown = 80

    def update(self, collisions, players, bounds=None):
        super().update(collisions, players, bounds)
        if not self.alive:
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
            self.shoot_cooldown = 90

        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if projectile.update(collisions, players, bounds)
        ]

    def draw(self, surface):
        super().draw(surface)
        for projectile in self.projectiles:
            projectile.draw(surface)
