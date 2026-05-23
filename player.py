import pygame

class Player:
    def __init__(self, x, y, sprite_path, controls):
        self.spritesheet = pygame.image.load(sprite_path).convert_alpha()
        self.frame_w = 125
        self.frame_h = 166
        self.x = x
        self.y = y
        self.speed = 3
        self.frame = 0
        self.direction = 0
        self.flip = False
        self.controls = controls
        self.hp = 100
        self.invulnerability_timer = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, 48, 64)

    def get_frame(self):
        return self.spritesheet.subsurface((
            self.frame * self.frame_w,
            self.direction * self.frame_h,
            self.frame_w,
            self.frame_h
        ))

    def update(self, collisions=[]):
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1

        keys = pygame.key.get_pressed()
        moved = False
        old_x, old_y = self.x, self.y

        if keys[self.controls["left"]]:
            self.x -= self.speed
            self.direction = 1
            self.flip = True
            moved = True
        if keys[self.controls["right"]]:
            self.x += self.speed
            self.direction = 1
            self.flip = False
            moved = True
        if keys[self.controls["up"]]:
            self.y -= self.speed
            moved = True
        if keys[self.controls["down"]]:
            self.y += self.speed
            moved = True

        rect = pygame.Rect(self.x, self.y, 48, 64)
        for wall in collisions:
            if rect.colliderect(wall):
                self.x, self.y = old_x, old_y
                break

        if moved:
            self.frame = (self.frame + 1) % 4

    def take_hit(self, from_x=None, from_y=None, damage=10, collisions=None, bounds=None):
        if self.invulnerability_timer > 0:
            return False
        self.hp = max(0, self.hp - damage)
        self.invulnerability_timer = 45
        if from_x is not None and from_y is not None:
            dx = self.x + 24 - from_x
            dy = self.y + 32 - from_y
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            self._safe_knockback(
                int(12 * dx / dist),
                int(12 * dy / dist),
                collisions or [],
                bounds,
            )
        return True

    def _safe_knockback(self, dx, dy, collisions, bounds):
        old_x, old_y = self.x, self.y

        self.x += dx
        if self._blocked(collisions, bounds):
            self.x = old_x

        self.y += dy
        if self._blocked(collisions, bounds):
            self.y = old_y

    def _blocked(self, collisions, bounds):
        rect = self.rect
        if bounds and not bounds.contains(rect):
            return True
        return any(rect.colliderect(wall) for wall in collisions)

    def draw(self, surface):
        frame = self.get_frame()
        frame = pygame.transform.scale(frame, (48, 64))
        frame = pygame.transform.flip(frame, self.flip, False)
        if self.invulnerability_timer > 0 and (self.invulnerability_timer // 5) % 2 == 0:
            frame = frame.copy()
            frame.fill((255, 80, 80, 90), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(frame, (self.x, self.y))

        bar_w = 48
        hp_w = int(bar_w * (self.hp / 100))
        pygame.draw.rect(surface, (60, 20, 20), (self.x, self.y - 8, bar_w, 5))
        pygame.draw.rect(surface, (80, 220, 90), (self.x, self.y - 8, hp_w, 5))

    def to_network_state(self):
        return {
            "x": int(self.x),
            "y": int(self.y),
            "direction": int(self.direction),
            "frame": int(self.frame),
            "flip": bool(self.flip),
        }

    def apply_network_state(self, state):
        self.x = int(state.get("x", self.x))
        self.y = int(state.get("y", self.y))
        self.direction = int(state.get("direction", self.direction))
        self.frame = int(state.get("frame", self.frame))
        self.flip = bool(state.get("flip", self.flip))
