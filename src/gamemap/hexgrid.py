'''
Created on Jul 9, 2012

@author: Chris
'''
from util.tools import Loc
import math

WEST = 0
NORTHWEST = 1
NORTHEAST = 2
EAST = 3
SOUTHEAST = 4
SOUTHWEST = 5

#neighbors = [(-1, -1), (0, -1), (1, 0), (1, 1), (0, 1), (-1, 0)]
neighbor_deltas = [(-1, 0), (-1, -1), (0, -1), (1, 0), (0, 1), (-1, 1) ]
midpt_deltas = [(-1, 0), (-0.5, -0.866), (0.5, -0.866), (1, 0), (0.5, 0.866), (-0.5, 0.866)]
odd_row_neighbors = [(-1, 0), (-1, -1), (0, -1), (1, 0), (0, 1), (-1, 1) ]
even_row_neighbors = [(-1, 0), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1)  ]
#                      0, 0    +1, 0    +1, 0    0, 0    +1, 0,  +1, 0: if even row and not E or W, add 1 to deltas
#                    OR: if y % 2 == 0 and direction % 3 > 0: x += 1 


# get neighbor of loc in direction dir
def get_neighbor(loc, dir):
    if loc.y % 2 != 0:
        x_offset, y_offset = even_row_neighbors[dir]
    else:
        x_offset, y_offset = odd_row_neighbors[dir]
    return (loc.x + x_offset, loc.y + y_offset)

# take input array coordinates and return hex neighbors (also in array coordinates)
def get_neighbor_coords(loc, width, height):
    neighbors = []
    for direction in range(len(neighbor_deltas)):
        x, y = loc.x + neighbor_deltas[direction][0], loc.y + neighbor_deltas[direction][1]
        if loc.y % 2 != 0 and direction % 3 != 0:
            x += 1
        if  x >= 0 and x < width and y >= 0 and y < height:
            neighbors.append(Loc(x, y))
    
    return neighbors
 
def get_coords_in_radius(x, y, width, height):
    return None

# find the reverse direction from a given direction
def get_reverse(direction):
    return (direction + 3) % 6

def get_distance(loc0, loc1):
        x0, x1 = loc0.x, loc1.x
        y0, y1 = loc0.y, loc1.y
        
        dx = x1 - x0 - math.floor(y1 / 2.0) + math.floor(y0 / 2.0)
        dy = y1 - y0

        if cmp(dx, 0) == cmp(dy, 0):
            return int(abs(dx + dy))
        else:
            return int(max(abs(dx), abs(dy)))    

# get angle between -5 and 5
def get_angle(dir1, dir2):
    return dir1 - dir2

# get angle between 0 (same direction) and 3 (opposite direction)
def get_abs_angle(dir1, dir2):
    angle = abs (dir2 - dir1)
    if angle > 3:
        angle = 6 - angle
    return angle

# get angle between 0 (same direction) and 5 (dir 2 is almost all the way around the clock from dir 1)
def get_clock_angle(dir1, dir2):
    return (dir2 - dir1) % 6

def side_midpt(center, hex_size, direction):
    x_delta, y_delta = midpt_deltas[direction]
    return center[0] + x_delta * hex_size, center[1] + y_delta * hex_size

# find the direction needed to get from loc1 to loc2
def get_direction(loc1, loc2):
    dx = loc2.x - loc1.x
    dy = loc2.y - loc1.y
    
    if loc1.y % 2 != 0:
        deltas = even_row_neighbors
    else:
        deltas = odd_row_neighbors
    
    for i in range(len(deltas)):
        if (dx, dy) == deltas[i]:
            return i
    
    raise ValueError("locations provided to get_direction not adjacent: " + str(loc1.x) + "," + str(loc1.y) + " " + str(loc2.x) + "," + str(loc2.y))  