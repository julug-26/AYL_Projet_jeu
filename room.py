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
        self.wall_replace_active = True
        self.wall_replace_collisions = []
        self.anim_timer = 0

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
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "WALL REPLACE":
                for x, y, gid in layer:
                    if gid:
                        r = pygame.Rect(
                            x * self.tile_width,
                            y * self.tile_height,
                            self.tile_width,
                            self.tile_height
                        )
                        self.wall_replace_collisions.append(r)
                        self.collisions.append(r)

        for obj in self.data.objects:
            if obj.type == "collectible":
                self.items.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "visible": True
                })
            elif obj.type == "porte":
                self.doors.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "target": obj.properties.get("target", None)
                })
            elif obj.type == "plaque":
                self.plaques.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                })

    def draw(self, surface, dt):
        self.anim_timer += dt

        for layer in self.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if layer.name == "WALL REPLACE" and not self.wall_replace_active:
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
            if p1_on and p2_on:
                return "both", door["target"]
            elif p1_on or p2_on:
                return "one", door["name"]
        return None, None

    def check_plaques(self, rect1, rect2):
        for plaque in self.plaques:
            if rect1.colliderect(plaque["rect"]) or rect2.colliderect(plaque["rect"]):
                self.wall_replace_active = False
                for r in self.wall_replace_collisions:
                    if r in self.collisions:
                        self.collisions.remove(r)
                return
        self.wall_replace_active = True
        for r in self.wall_replace_collisions:
            if r not in self.collisions:
                self.collisions.append(r)