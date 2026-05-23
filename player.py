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

    def get_frame(self):
        return self.spritesheet.subsurface((
            self.frame * self.frame_w,
            self.direction * self.frame_h,
            self.frame_w,
            self.frame_h
        ))

    def update(self, collisions=[]):
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

    def draw(self, surface):
        frame = self.get_frame()
        frame = pygame.transform.scale(frame, (48, 64))
        frame = pygame.transform.flip(frame, self.flip, False)
        surface.blit(frame, (self.x, self.y))

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
