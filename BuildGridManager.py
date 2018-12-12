import numpy as np

class BuildGrid(object):
    def __init__(self):
        self.building_grid = np.zeros((1,1))

    def populate_map_grid(self, playable_map_area):
        self.building_grid = np.zeros(playable_map_area)
        for x in range(self.building_grid.shape[0]):
            for y in range(self.building_grid.shape[1]):
                grid_loc = (x,y)
                if self.in_placement_grid(grid_loc) is True:
                    self.building_grid[x][y] = 1

    def in_placement_grid(self, pos) -> bool:
        """Returns True if position is buildable"""
        return self._game_info.placement_grid[pos] != 0

    def get_build_loc(self, building_grid):
        """Retrieves arbitrary buildling location for buildings."""
        #TODO 11/25/2018 - Specialized building location (gas, supply depot, structures, base design
        self.find_depot_placement(self.building_grid)
                    
    def find_depot_placement(self, grid):
        tile_list = []
        for x in range(grid.shape[0]-1):
            for y in range(grid.shape[1]-1):
                if grid[x][y] == 1:
                    start = grid[x][y]
                    down = grid[x+1][y]
                    bot_right = grid[x+1][y+1]
                    right = grid[x][y+1]
                    if self.check_map_bounds(grid, start, down, bot_right, right) is True:
                        tile = (x,y)
                        tile_list.append(tile)
        return tile_list

    def check_map_bounds(self, grid, *args):
            for tile in args:
                if tile not in grid:
                    return False
                else:
                    pass
            return True

