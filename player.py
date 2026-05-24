import pygame
import os
import re

ANIM_SPEED = 8  # ticks de jeu entre chaque frame d'animation (60fps / 8 ≈ 7.5fps)
SPRITE_SIZE = (48, 64)  # taille d'affichage et de collision

J1_ANIM_MAP = {
    "idle":             "pose immobile",
    "droite":           "mouvement_droite",
    "gauche":           "mouvement_gauche",
    "dos":              "mouvement_dos",
    "face":             "mouvement_face",
    "diag_haut_droite": "mouvement_diagonale_haut_droite",
    "diag_haut_gauche": "mouvement_diagonale_haut_gauche",
    "diag_bas_droite":  "mouvement_diagonale_bas_droite",
    "diag_bas_gauche":  "mouvement_diagonale_bas_gauche",
    "attaque_droite":   "mvt attaque droite",
    "attaque_gauche":   "mvt_attaque_gauche",
}

J2_ANIM_MAP = {
    "idle":             "sprite_immobile",
    "droite":           "mvt_cote_droit",
    "gauche":           "mvt_cote_gauche",
    "dos":              "mvt_dos",
    "face":             "mvt_de_face",
    "diag_haut_droite": "mvt_diagonale_haut_droit",
    "diag_haut_gauche": "mvt_diagonale_haut_gauche",
    "diag_bas_droite":  "mvt_diagonale_bas_droite",
    "diag_bas_gauche":  "mvt_diagonale_bas_gauche",
    "attaque_droite":   "mvt_attaque_droite",
    "attaque_gauche":   "mvt_attaque_gauche",
}


def _load_dir_frames(dir_path):
    """Charge tous les PNG d'un dossier, triés par valeur numérique dans le nom."""
    if not os.path.isdir(dir_path):
        return []
    files = [f for f in os.listdir(dir_path) if f.lower().endswith('.png')]

    def sort_key(name):
        nums = re.findall(r'\d+', name)
        return [int(n) for n in nums] if nums else [0]

    files.sort(key=sort_key)
    frames = []
    for f in files:
        try:
            frames.append(pygame.image.load(os.path.join(dir_path, f)).convert_alpha())
        except Exception:
            pass
    return frames


class Player:
    def __init__(self, x, y, sprite_path, controls, anim_map=None):
        self.x = x
        self.y = y
        self.speed = 3
        self.controls = controls
        self.hp = 100
        self.invulnerability_timer = 0
        self.attack_cooldown = 0

        # direction / flip : conservés pour état réseau et héritage
        self.direction = 0
        self.flip = False

        # Champs héritage spritesheet
        self.spritesheet = None
        self.frame = 0
        self.frame_w = 125
        self.frame_h = 166

        # Nouveau système d'animation par dossiers
        self.animations = {}
        self.anim_key = "face"  # direction par défaut au démarrage
        self.anim_frame = 0
        self.anim_tick = 0
        self.is_attacking = False

        if anim_map and os.path.isdir(sprite_path):
            for key, subdir in anim_map.items():
                frames = _load_dir_frames(os.path.join(sprite_path, subdir))
                if frames:
                    self.animations[key] = frames
        else:
            self.spritesheet = pygame.image.load(sprite_path).convert_alpha()

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, SPRITE_SIZE[0], SPRITE_SIZE[1])

    def _get_move_key(self, keys):
        left  = keys[self.controls["left"]]
        right = keys[self.controls["right"]]
        up    = keys[self.controls["up"]]
        down  = keys[self.controls["down"]]

        if right and up:   return "diag_haut_droite"
        if right and down: return "diag_bas_droite"
        if left and up:    return "diag_haut_gauche"
        if left and down:  return "diag_bas_gauche"
        if right:          return "droite"
        if left:           return "gauche"
        if up:             return "dos"
        if down:           return "face"
        return None

    def _advance_anim(self, new_key, loop=True):
        """Change d'animation si besoin, avance la frame. Retourne True quand l'anim non-loopée est finie."""
        if new_key != self.anim_key:
            self.anim_key = new_key
            self.anim_frame = 0
            self.anim_tick = 0
            return False

        frames = self.animations.get(self.anim_key, [])
        if not frames:
            return True

        self.anim_tick += 1
        if self.anim_tick >= ANIM_SPEED:
            self.anim_tick = 0
            self.anim_frame += 1
            if self.anim_frame >= len(frames):
                if loop:
                    self.anim_frame = 0
                else:
                    self.anim_frame = len(frames) - 1
                    return True
        return False

    def get_frame(self):
        if self.animations:
            frames = self.animations.get(self.anim_key) or self.animations.get("face", [])
            if frames:
                return frames[min(self.anim_frame, len(frames) - 1)]
            return None
        return self.spritesheet.subsurface((
            self.frame * self.frame_w,
            self.direction * self.frame_h,
            self.frame_w,
            self.frame_h
        ))

    def update(self, collisions=[]):
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        keys = pygame.key.get_pressed()
        old_x, old_y = self.x, self.y
        moved = False

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

        rect = pygame.Rect(self.x, self.y, SPRITE_SIZE[0], SPRITE_SIZE[1])
        for wall in collisions:
            if rect.colliderect(wall):
                self.x, self.y = old_x, old_y
                break

        if self.animations:
            if self.is_attacking:
                attack_key = "attaque_gauche" if self.flip else "attaque_droite"
                done = self._advance_anim(attack_key, loop=False)
                if done:
                    self.is_attacking = False
            else:
                move_key = self._get_move_key(keys)
                if move_key:
                    self._advance_anim(move_key, loop=True)
                else:
                    # Immobile : fige sur la frame 0 de la dernière direction
                    self.anim_frame = 0
                    self.anim_tick = 0
        else:
            if moved:
                self.frame = (self.frame + 1) % 4

    def start_attack(self):
        self.attack_cooldown = 35
        if self.animations:
            attack_key = "attaque_gauche" if self.flip else "attaque_droite"
            if attack_key in self.animations:
                self.is_attacking = True
                self.anim_key = attack_key
                self.anim_frame = 0
                self.anim_tick = 0

    def can_attack(self):
        return self.attack_cooldown <= 0

    def start_attack_cooldown(self):
        self.attack_cooldown = 35

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
        if frame is None:
            return
        frame = pygame.transform.scale(frame, SPRITE_SIZE)
        if not self.animations:
            frame = pygame.transform.flip(frame, self.flip, False)
        if self.invulnerability_timer > 0 and (self.invulnerability_timer // 5) % 2 == 0:
            frame = frame.copy()
            frame.fill((255, 80, 80, 90), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(frame, (self.x, self.y))

        bar_w = SPRITE_SIZE[0]
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
            "anim_key": self.anim_key,
            "anim_frame": int(self.anim_frame),
        }

    def apply_network_state(self, state):
        self.x = int(state.get("x", self.x))
        self.y = int(state.get("y", self.y))
        self.direction = int(state.get("direction", self.direction))
        self.frame = int(state.get("frame", self.frame))
        self.flip = bool(state.get("flip", self.flip))
        self.anim_key = state.get("anim_key", self.anim_key)
        self.anim_frame = int(state.get("anim_frame", self.anim_frame))
