import numpy as np
from typing import List
"""
MicroController utilizes different types of pathfinding algorithms.
"""
class Micro(object):
    def harass_micro(self, friendly_unit_pos, enemy_worker_pos, closest_enemy_unit_pos): #Function currently isn't being used.
        '''Creates a dynamic position returned as a vector. The vector is created from the sum of a normalized
        attraction vector(enemy worker) and repulsion vector (closest enemy unit).'''
        if enemy_worker_pos is None:
            enemy_worker_pos = np.array([0, 0])
        if closest_enemy_unit_pos is None:
            closest_enemy_unit_pos = np.array([0, 0])
        #Compute attraction & repulsion vector inputs as 2d arrays.
        harass_repulsion_vec = np.array(friendly_unit_pos) - np.array(closest_enemy_unit_pos)
        harass_attract_vec = np.array(enemy_worker_pos) - np.array(friendly_unit_pos)
        #normalize
        norm_harass_repulsion_vec = harass_repulsion_vec / np.linalg.norm(harass_repulsion_vec)
        norm_harass_attract_vec = harass_attract_vec / np.linalg.norm(harass_attract_vec)
        #Final harass vector
        final_harass_vec = norm_harass_attract_vec + (norm_harass_repulsion_vec*3)
        return final_harass_vec

    def harass_micro_avg(self, friendly_unit_pos, enemy_workers_pos: List, closest_enemy_unit_pos):
        '''updated function from harass_micro to accommodate multiple enemy workers'''
        if enemy_workers_pos is None:
            enemy_workers_pos = np.array([0, 0])
        if closest_enemy_unit_pos is None:
            closest_enemy_unit_pos = np.array([0, 0])

        #Compute attraction & repulsion vector inputs as 2d arrays.
        harass_repulsion_vec = np.array(friendly_unit_pos) - np.array(closest_enemy_unit_pos)
        harass_attract_vec = np.array(enemy_workers_pos).mean(axis=0) - np.array(friendly_unit_pos)
        #normalize
        norm_harass_repulsion_vec = harass_repulsion_vec / np.linalg.norm(harass_repulsion_vec)
        norm_harass_attract_vec = harass_attract_vec / np.linalg.norm(harass_attract_vec)
        #Final harass vector
        final_harass_vec = norm_harass_attract_vec + (norm_harass_repulsion_vec*3)
        return final_harass_vec

#WIP - 10/14/2018
#unit = (2,2)    #list of friendly unit positions
#enemy = (5,5)   #list of enemy unit positions
#radius = 2  #radius == unit.ground_range
#map = np.zeros((9, 9))
#intensity = 2   #intensity == unit.health + unit.shield / unit.ground_dps
#enemy_intensity = 4 #intensity == unit.health + unit.shield / unit.ground_dps

    def influence_map(self, playable_area, radius, intensity, enemy_unit_pos):
        #Takes (x,y) position of closest enemy unit and adds field of influence onto a zeros numpy array.
        map = np.zeros(playable_area)   # returns this as the influence map
        unit_pos_x = enemy_unit_pos[0]  # x position
        unit_pos_y = enemy_unit_pos[1]  # y position
        #map_pos = np.array([x, y])     # doesn't appear to be used at this time.
        unit_pos = np.array([unit_pos_x, unit_pos_y])

        for x in range(radius*3):
            for y in range(radius*3):
                #enemy_x_pos = enemy[0]
                #enemy_y_pos = enemy[1]
                #enemy_unit_pos = np.array([enemy_x_pos, enemy_y_pos])
                x_range = map.shape[0]
                y_range = map.shape[1]
                friendly_dist = np.linalg.norm(map_pos - unit_pos)  # position 1 - position 2
                #enemy_dist = np.linalg.norm(map_pos - enemy_unit_pos)

                friendly_interpolated_value = intensity * max(0,(radius - round(friendly_dist,2)))   #This has to never be < 0
                #enemy_interpolated_value = enemy_intensity * max(0, (radius - round(enemy_dist,2)))

                if x + unit_pos_x - radius < x_range and y + unit_pos_y - radius < y_range:
                    map[x + unit_pos_x - radius][y + unit_pos_y - radius] += friendly_interpolated_value
                #if x + enemy_x_pos - radius < x_range and y + enemy_y_pos - radius < y_range:
                    #map[x + enemy_x_pos - radius][y + enemy_y_pos - radius] += enemy_interpolated_value
                #print(map)
                #map[x + aa - radius][y + bb - radius] += enemy_interpolated_value

    def rolling_window(main_array, sub_array_shape, stepsize_x=1, stepsize_y=1): 
        strided = np.lib.stride_tricks.as_strided
        x_sub_dim, y_sub_dim = sub_array_shape  #Define custom sub_array_shape for rolling window.  
        x_main_dim,y_main_dim = main_array.shape[-2:]    # List slice ensures that multi-dimension is not affected
        #print(x_main_dim, "x_main_dim", y_main_dim, "y_main_dim")
        #print(x_sub_dim, "x_sub_dim", y_sub_dim, "y_sub_dim")
        x_main_stride,y_main_stride = main_array.strides[-2:]

        out_shp = main_array.shape[:-2] + (x_main_dim - x_sub_dim + 1, y_main_dim - y_sub_dim + 1, x_sub_dim, y_sub_dim)
        out_stride = main_array.strides[:-2] + (x_main_stride, y_main_stride, x_main_stride, y_main_stride)

        imgs = strided(main_array, shape=out_shp, strides=out_stride)
        return imgs[...,::stepsize_x,::stepsize_y,:,:]

