import pytmx
import pygame
from settings import *

class TiledMap:
    def __init__(self, filename):
        self.tmx_data = pytmx.load_pygame(
            filename,
            pixelalpha=True,
            allow_flipped_tiles=False
        )
        self.width  = self.tmx_data.width  * TILE_SIZE
        self.height = self.tmx_data.height * TILE_SIZE

    def render(self, surface):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    try:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            surface.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
                    except Exception:
                        pass

    def make_map(self):
        temp_surface = pygame.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface

    def get_collision_grid(self):
        grid = []
        for y in range(self.tmx_data.height):
            row = []
            for x in range(self.tmx_data.width):
                try:
                    tile = self.tmx_data.get_tile_gid(x, y,
                           self.tmx_data.get_layer_by_name(WALL_LAYER))
                    row.append(1 if tile else 0)
                except Exception:
                    row.append(0)
            grid.append(row)
        return grid