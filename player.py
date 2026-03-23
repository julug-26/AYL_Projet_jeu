import pygame

class Player:
    def __init__(self, x, y):
        self.spritesheet = pygame.image.load("assets/spritepersobleu.png").convert_alpha()
        self.frame_w = 125
        self.frame_h = 166
        self.x = x
        self.y = y
        self.speed = 3
        self.frame = 0
        self.direction = 0
        self.flip = False

    def get_frame(self):
        return self.spritesheet.subsurface((
            self.frame * self.frame_w,
            self.direction * self.frame_h,
            self.frame_w,
            self.frame_h
        ))

    def update(self):
        keys = pygame.key.get_pressed()
        moved = False

        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = 1
            self.flip = True
            moved = True
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = 1
            self.flip = False
            moved = True
        if keys[pygame.K_UP]:
            self.y -= self.speed
            moved = True
        if keys[pygame.K_DOWN]:
            self.y += self.speed
            moved = True

        if moved:
            self.frame = (self.frame + 1) % 4

    def draw(self, surface):
        frame = self.get_frame()
        frame = pygame.transform.scale(frame, (48, 64))
        frame = pygame.transform.flip(frame, self.flip, False)
        surface.blit(frame, (self.x, self.y))