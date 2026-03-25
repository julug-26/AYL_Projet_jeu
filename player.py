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

    def get_input(self):
        """Prépare les inputs à envoyer au serveur."""
        keys = pygame.key.get_pressed()
        dx = dy = 0
        moved = False

        if keys[self.controls["left"]]:
            dx -= self.speed
            self.direction = 1
            self.flip = True
            moved = True
        if keys[self.controls["right"]]:
            dx += self.speed
            self.direction = 1
            self.flip = False
            moved = True
        if keys[self.controls["up"]]:
            dy -= self.speed
            moved = True
        if keys[self.controls["down"]]:
            dy += self.speed
            moved = True

        if moved:
            self.frame = (self.frame + 1) % 4

        # On envoie la nouvelle position proposée
        return {
            "x": self.x + dx,
            "y": self.y + dy
        }

    def apply_state(self, state_dict):
        """Applique la position officielle venant du serveur."""
        self.x = state_dict.get("x", self.x)
        self.y = state_dict.get("y", self.y)

    def draw(self, surface):
        frame = self.get_frame()
        frame = pygame.transform.scale(frame, (48, 64))
        frame = pygame.transform.flip(frame, self.flip, False)
        surface.blit(frame, (self.x, self.y))
