import pygame
import pytmx

class Room:
    def __init__(self, tmx_path):
        self.data = pytmx.load_pygame(tmx_path)
        self.tile_width = self.data.tilewidth
        self.tile_height = self.data.tileheight
        self.collisions = []
        self.items = []

        for layer in self.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "wall":
                for x, y, gid in layer:
                    if gid:
                        self.collisions.append(pygame.Rect(
                            x * self.tile_width,
                            y * self.tile_height,
                            self.tile_width,
                            self.tile_height
                        ))

        for obj in self.data.objects:
            if obj.type == "collectible":
                self.items.append({
                    "name": obj.name,
                    "rect": pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    "visible": True
                })

    def draw(self, surface):
        for layer in self.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
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