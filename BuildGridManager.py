from sc2.game_info import GameInfo
import numpy as np

"""
BuildGridManager queries the building_grid to find building locations based on different criteria. 
"""
class BuildGrid(object):    

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

