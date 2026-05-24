import pygame
import pytmx

class Room:
    def __init__(self, tmx_path):
        self.data = pytmx.load_pygame(tmx_path)
        self.tile_width = self.data.tilewidth
        self.tile_height = self.data.tileheight
        self.collisions = []
        self.items = []
        self.doors = []
        self.plaques = []
        self.leviers = []
        self.spawn_points = {}
        self.wall_replace_active = True
        self.wall_replace_collisions = []
        self.wall_replace_levier_locked = False
        self.wall_replace2_active = True
        self.wall_replace2_collisions = []
        self.wall_replace2_levier_locked = False
        self.wall_replace3_active = True
        self.wall_replace3_collisions = []
        self.wall_replace4_active = True
        self.wall_replace4_collisions = []
        self.wall_replace5_active = True
        self.wall_replace5_collisions = []
        self.wall_bloque_active = False
        self.wall_bloque_collisions = []
        self.anim_timer = 0
        self.spawn = None
        self.both_plaques_required = False
        self.plaque1_locked = False
        self.plaque2_locked = False
        self.plaque3_locked = False
        self.plaque4_locked = False
        self.plaques34_locked = False
        self.levier1_activated = False
        self.levier2_activated = False
        self.levier3_activated = False

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name in ("wall tuiles", "wall"):
                for x, y, gid in layer:
                    if gid:
                        self.collisions.append(pygame.Rect(
                            x * self.tile_width,
                            y * self.tile_height,
                            self.tile_width,
                            self.tile_height
                        ))

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name in ("WALL REPLACE", "wall replace 1"):
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_replace_collisions.append(r)
                        self.collisions.append(r)

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall replace 2":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_replace2_collisions.append(r)
                        self.collisions.append(r)

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall replace 3":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_replace3_collisions.append(r)
                        self.collisions.append(r)

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall replace 4":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_replace4_collisions.append(r)
                        self.collisions.append(r)

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall replace 5":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_replace5_collisions.append(r)
                        self.collisions.append(r)

        for layer in self.data.layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall bloque":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(x * self.tile_width, y * self.tile_height, self.tile_width, self.tile_height)
                        self.wall_bloque_collisions.append(r)

        for obj in self.data.objects:
            if obj.type == "collectible":
                self.items.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "visible": True
                })
            elif obj.type in ("porte", "portail"):
                self.doors.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "target": obj.properties.get("target", None),
                    "is_portail": obj.type == "portail"
                })
            elif obj.type == "plaque":
                self.plaques.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                })
            elif obj.type == "levier":
                self.leviers.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "activated": False
                })
            elif obj.type in ("spawn", "spawn ennemie", "spawn joueur", "spawn boss"):
                self.spawn_points[obj.name] = (obj.x, obj.y)
                if obj.type == "spawn":
                    self.spawn = (obj.x, obj.y)

        self.base_collisions = list(self.collisions)

    def reset_state(self):
        self.collisions = list(self.base_collisions)
        self.wall_replace_active = True
        self.wall_replace_levier_locked = False
        self.wall_replace2_active = True
        self.wall_replace2_levier_locked = False
        self.wall_replace3_active = True
        self.wall_replace4_active = True
        self.wall_replace5_active = True
        self.wall_bloque_active = False
        self.plaque1_locked = False
        self.plaque2_locked = False
        self.plaque3_locked = False
        self.plaque4_locked = False
        self.plaques34_locked = False
        self.levier1_activated = False
        self.levier2_activated = False
        self.levier3_activated = False

        for item in self.items:
            item["visible"] = True
        for levier in self.leviers:
            levier["activated"] = False

    def draw(self, surface, dt, p1_rect=None, p2_rect=None):
        self.anim_timer += dt
        on_plaque = False
        if p1_rect and p2_rect:
            on_plaque = any(
                p1_rect.colliderect(p["rect"]) or p2_rect.colliderect(p["rect"])
                for p in self.plaques
            )

        p1_on_p1 = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
        p2_on_p1 = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
        p1_on_p2 = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")
        p2_on_p2 = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")
        both_plaques_on = (p1_on_p1 or p2_on_p1) and (p1_on_p2 or p2_on_p2)
        any_plaque12_on = (p1_on_p1 or p2_on_p1 or p1_on_p2 or p2_on_p2)

        p1_on_p3 = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 3")
        p2_on_p3 = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 3")
        p1_on_p4 = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 4")
        p2_on_p4 = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 4")

        for layer in self.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if layer.name in ("WALL REPLACE", "wall replace 1") and not self.wall_replace_active:
                    continue
                if layer.name == "wall replace 2" and not self.wall_replace2_active:
                    continue
                if layer.name == "wall replace 3" and not self.wall_replace3_active:
                    continue
                if layer.name == "wall replace 4" and not self.wall_replace4_active:
                    continue
                if layer.name == "wall replace 5" and not self.wall_replace5_active:
                    continue
                if layer.name == "wall bloque" and not self.wall_bloque_active:
                    continue
                if layer.name == "inverse plaque" and not on_plaque:
                    continue
                if layer.name == "plaque 1":
                    p1_on = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
                    p2_on = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
                    if not self.plaque1_locked and not (p1_on or p2_on):
                        continue
                if layer.name == "plaque 2":
                    p1_on = p1_rect and any(p1_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")
                    p2_on = p2_rect and any(p2_rect.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")
                    if not self.plaque2_locked and not (p1_on or p2_on):
                        continue
                if layer.name == "plaque 3":
                    if not self.plaque3_locked and not (p1_on_p3 or p2_on_p3):
                        continue
                if layer.name == "plaque 4":
                    if not self.plaque4_locked and not (p1_on_p4 or p2_on_p4):
                        continue
                if layer.name == "plaque 1 et 2":
                    if not any_plaque12_on:
                        continue
                if layer.name == "levier 1 actif" and not self.levier1_activated:
                    continue
                if layer.name == "levier 1 inactif" and self.levier1_activated:
                    continue
                if layer.name == "levier 2 actif" and not self.levier2_activated:
                    continue
                if layer.name == "levier 2 inactif" and self.levier2_activated:
                    continue
                if layer.name == "levier 3 actif" and not self.levier3_activated:
                    continue
                if layer.name == "levier 3 inactif" and self.levier3_activated:
                    continue

                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile_props = self.data.get_tile_properties_by_gid(gid)
                    if tile_props and "frames" in tile_props:
                        frames = tile_props["frames"]
                        total_duration = sum(f.duration for f in frames)
                        t = self.anim_timer % total_duration
                        elapsed = 0
                        current_gid = frames[0].gid
                        for f in frames:
                            elapsed += f.duration
                            if t < elapsed:
                                current_gid = f.gid
                                break
                        tile = self.data.get_tile_image_by_gid(current_gid)
                    else:
                        tile = self.data.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * self.tile_width, y * self.tile_height))

    def check_items(self, player_rect):
        collected = []
        for item in self.items:
            if item["visible"] and player_rect.colliderect(item["rect"]):
                item["visible"] = False
                collected.append(item["name"])
        return collected

    def check_doors(self, rect1, rect2):
        for door in self.doors:
            p1_on = rect1.colliderect(door["rect"])
            p2_on = rect2.colliderect(door["rect"])
            is_portail = door.get("is_portail", False)
            if p1_on and p2_on and not is_portail:
                target = door["target"] if door["target"] else door["name"]
                return "both", target, None
            elif (p1_on or p2_on) and is_portail:
                target = door["target"] if door["target"] else door["name"]
                trigger = "p1" if p1_on else "p2"
                return "portail", target, trigger
            elif p1_on or p2_on:
                return "one", door["name"], None
        return None, None, None

    def check_plaques(self, rect1, rect2):
        if self.both_plaques_required:
            if self.wall_bloque_active:
                return
            p1_on_p1 = any(rect1.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
            p2_on_p1 = any(rect2.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 1")
            p1_on_p2 = any(rect1.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")
            p2_on_p2 = any(rect2.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 2")

            plaque1_active = p1_on_p1 or p2_on_p1 or self.plaque1_locked
            plaque2_active = p1_on_p2 or p2_on_p2 or self.plaque2_locked

            if plaque1_active and plaque2_active:
                self.plaque1_locked = True
                self.plaque2_locked = True
                self.wall_replace_active = False
                for r in self.wall_replace_collisions:
                    if r in self.collisions:
                        self.collisions.remove(r)
                self.wall_bloque_active = True
                for r in self.wall_bloque_collisions:
                    if r not in self.collisions:
                        self.collisions.append(r)
        else:
            p1_on = any(rect1.colliderect(p["rect"]) for p in self.plaques if p["name"] in ("plaque 1", "plaque 2"))
            p2_on = any(rect2.colliderect(p["rect"]) for p in self.plaques if p["name"] in ("plaque 1", "plaque 2"))
            if p1_on or p2_on:
                self.wall_replace3_active = False
                for r in self.wall_replace3_collisions:
                    if r in self.collisions:
                        self.collisions.remove(r)
            else:
                self.wall_replace3_active = True
                for r in self.wall_replace3_collisions:
                    if r not in self.collisions:
                        self.collisions.append(r)

            if not self.plaques34_locked:
                p1_on_p3 = any(rect1.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 3")
                p2_on_p3 = any(rect2.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 3")
                p1_on_p4 = any(rect1.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 4")
                p2_on_p4 = any(rect2.colliderect(p["rect"]) for p in self.plaques if p["name"] == "plaque 4")
                plaque3_on = p1_on_p3 or p2_on_p3
                plaque4_on = p1_on_p4 or p2_on_p4
                if plaque3_on and plaque4_on:
                    self.plaques34_locked = True
                    self.plaque3_locked = True
                    self.plaque4_locked = True
                    self.wall_replace4_active = False
                    for r in self.wall_replace4_collisions:
                        if r in self.collisions:
                            self.collisions.remove(r)

    def activate_levier(self, player_rect, levier_name):
        for levier in self.leviers:
            if not levier["activated"] and levier["name"] == levier_name and player_rect.colliderect(levier["rect"].inflate(20, 20)):
                levier["activated"] = True
                if levier_name == "levier 1":
                    self.levier1_activated = True
                    self.wall_replace_active = False
                    self.wall_replace_levier_locked = True
                    for r in self.wall_replace_collisions:
                        if r in self.collisions:
                            self.collisions.remove(r)
                elif levier_name == "levier 2":
                    self.levier2_activated = True
                    self.wall_replace2_active = False
                    self.wall_replace2_levier_locked = True
                    for r in self.wall_replace2_collisions:
                        if r in self.collisions:
                            self.collisions.remove(r)
                elif levier_name == "levier 3":
                    self.levier3_activated = True
                    self.wall_replace5_active = False
                    for r in self.wall_replace5_collisions:
                        if r in self.collisions:
                            self.collisions.remove(r)