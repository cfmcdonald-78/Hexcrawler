import random, math
import hexgrid, hexmap, river, terrain
from heapq import heappush, heappop
from util.tools import * 
#import noise.perlin_noise as perlin_noise
'''
Created on Jun 6, 2012

@author: Chris
'''

        
class ProceduralMapmaker(object):
    '''
    classdocs
    '''
    def __init__(self, width, height): 
        self.width = width
        self.height = height
        
        self.EROSION_UNIT = 0.05    # determines how much height is transferred by each erosion
        self.RAIN_THRESHOLD = 0.15  # determines what % of hexes will get rain.  Highest 10%, 15%, 25%, etc.
        self.RIVER_THRESHOLD = 4    # determines how  much water needs to accumulate to start a river
        self.EDGE_RIVER_END_THRESHOLD = 0.10 # determines what % of edges will be potential river ends.  lowest 10%, 20%, etc.
        
        self.SEED_SCAN_RNG = 3     # determines how far terrain generators scan to see local terrain
        
        self.ZONE_SIZE = 10         # determines hex dimensions of zones on map
        
        # used padded width/height to generate terrain, then trim it to fit.  Avoids weird edge effects.
        self.PAD = 0
        self.padded_width = width  + self.PAD
        self.padded_height = height + self.PAD
        
        # elevation thresholds for terrain types
        self.sea_level = -0.5
        self.mountain_level = 0.8
        self.hill_level = 0.5
        
#    def find_lowest_neighbor(self, loc, heightmap):
#        neighbors = hexgrid.get_neighbor_coords(loc, self.padded_width, self.padded_height)
#        
#        def min_func(location):
#            return heightmap[location.x][location.y] 
#          
#        return min_in_list(neighbors, min_func)      
    
    # erode the given heightmap.  On average, each location will be eroded repeats # of times
    def erode_heightmap(self, heightmap, repeats):
        locs = []
        neighbors = {}
        for x in range(self.padded_width):
            for y in range(self.padded_height):
                new_loc = Loc(x,y)
                locs.append(new_loc)
                neighbors[new_loc] = hexgrid.get_neighbor_coords(new_loc, self.padded_width, self.padded_height)
        
        # erode results in order to create a smoother terrain - donate elevation from higher places to lower ones
        for i in range(self.padded_width * self.padded_height * repeats):
            # randomly choose a spot from which to start erosion
            hex_loc = random.choice(locs)
#            x, y = random.randint(0, self.padded_width - 1), random.randint(0, self.padded_height - 1)
            
            while True:
                lowest = min(neighbors[hex_loc], key = lambda hex_loc : heightmap[hex_loc.x][hex_loc.y])
#                lowest, lowest_elev = self.find_lowest_neighbor(Loc(x, y), heightmap)
                
                # make sure eroding will leave lowest neighbor lower than we are -
                # dirt can only slide downhill!
                if heightmap[lowest.x][lowest.y] + 2 * self.EROSION_UNIT >= heightmap[hex_loc.x][hex_loc.y]:
                    break
                
                # if there's a lower place to erode to, donate an erosion unit to it,
                heightmap[hex_loc.x][hex_loc.y] -= self.EROSION_UNIT
                heightmap[lowest.x][lowest.y] += self.EROSION_UNIT
                # see if we can continue eroding down from place we eroded to
                hex_loc = lowest
#                x = lowest.x
#                y = lowest.y
        return heightmap
    
    # use diamond square method
    def gen_heightmap(self, roughness, seed_function = None):
        def rand_in_range(rand_max):
            return rand_max * (random.random() * 2.0 - 1.0)
        def initial_seed(heightmap, x, y, seed_function):
            if seed_function != None:
                heightmap[x][y] = seed_function(x, y)
            else: 
                heightmap[x][y] = rand_in_range(rand_max)

        # pad map out to be square with sides of size power-of-2 + 1, so that diamond-square will work w/o special casing
        size = 1
        power = 0
        while size < self.padded_width or size < self.padded_height:
            power += 1
            size = (2 ** power) + 1
        
        heightmap = make_2D_list(size, size)
        rand_max = roughness

        # seed corners with random initial values
        initial_seed(heightmap, 0, 0, seed_function)
        initial_seed(heightmap, 0, size - 1, seed_function)
        initial_seed(heightmap, size - 1, 0, seed_function)
        initial_seed(heightmap, size - 1, size - 1, seed_function)
    
        side_size = size - 1
        seed_iters = 3
        while (side_size >= 2):
            # DIAMOND STEP: compute value at center of each square based on average of 4 corners + random value
            for y in range(0, size - 1, side_size):
                for x in range(0, size - 1, side_size):
                    if seed_function != None and seed_iters > 0:
                        # generating seed value rather than random value
                        new_value = seed_function(x + side_size / 2, y + side_size / 2)
                    else:
                        avg = (heightmap[x][y] + heightmap[x][y + side_size] + heightmap[x+ side_size][y] + heightmap[x + side_size][y + side_size]) / 4
                        new_value = avg + rand_in_range(rand_max)
                    heightmap[x + side_size / 2][y + side_size / 2] = new_value

            # SQUARE STEP: compute values on edges of each square based on average of surrounding diamond (only averaging 3 values if diamond goes off map)
            for y in range(0, size, side_size / 2):
                for x in range(0, size, side_size / 2):
                    # if value here has already been computed in previous step, skip it
                    if heightmap[x][y] != None:
                        continue
                    
                    num_vals = 0
                    total = 0
                    if x > 0:
                        num_vals += 1
                        total += heightmap[x - side_size / 2][y]
                    if y > 0:
                        num_vals += 1
                        total += heightmap[x][y  - side_size / 2]
                    if x < size - 1:
                        num_vals += 1
                        total += heightmap[x + side_size / 2][y]
                    if y < size - 1:
                        num_vals += 1
                        total += heightmap[x][y  + side_size / 2]      
                 
                    new_value = (total / num_vals) + rand_in_range(rand_max)
                    heightmap[x][y] = new_value
            
            # shrink down to next smallest size of square, reduce size of random variation, and continue   
            side_size = side_size / 2
            rand_max *= roughness  
            seed_iters -= 1
            
        return heightmap
    
    def find_river_path(self, start, targets, rivers, elevation):
        reach_cost = {}
        predecessor = {}
        open_locs = []
        closed_locs = []    
        
        heappush(open_locs, (0.0, start))
        reach_cost[start] = 0
        while len(open_locs) > 0:
            (curr_cost, curr_loc) = heappop(open_locs)
            curr_cost = reach_cost[curr_loc]
            closed_locs.append(curr_loc)
            curr_elev = elevation[curr_loc.x][curr_loc.y]
            
            # stop if we reach sea level, one of the lower board edges, or an existing river
            
            #end river if it reaches sea or low point on edge of map (targets), or existing river
            if curr_elev <= self.sea_level or curr_loc in targets or curr_loc in rivers:
                break
            
            neighbors = hexgrid.get_neighbor_coords(curr_loc, self.padded_width, self.padded_height)
            for neigh_loc in neighbors:
          
                # don't visit an already visited place or an already full-up river
                if neigh_loc in closed_locs or (neigh_loc in rivers and rivers[neigh_loc].num_inflows() >= river.MAX_INFLOWS):
                    continue
                    
                new_elev = elevation[neigh_loc.x][neigh_loc.y]
                if new_elev > curr_elev:
                    new_cost = curr_cost + (new_elev - curr_elev) * 2 # expensive to go up!
                else:
                    new_cost = curr_cost + (new_elev - curr_elev)
                    
                if (neigh_loc not in reach_cost) or (new_cost < reach_cost[neigh_loc]):
                    reach_cost[neigh_loc] = new_cost
                    predecessor[neigh_loc] = curr_loc
                    heappush(open_locs, (new_cost, neigh_loc)) 
        
        # translate search data into river entry/exit info for each hex in path. 
        # first, handle special case for river ending at map edge,
        # make it appear to go off map
        if curr_elev > self.sea_level and curr_loc in targets:
            # find direction of off map
            direction = -1
            if curr_loc.x == 0:
                direction = hexgrid.WEST
            if curr_loc.x == self.padded_width - 1:
                direction = hexgrid.EAST
            if curr_loc.y == 0:
                direction = hexgrid.NORTHEAST
            if curr_loc.y == self.padded_height - 1:
                direction = hexgrid.SOUTHWEST
            
            new_river = river.River() 
            new_river.set_outflow(direction)
            rivers[curr_loc] = new_river
      
        # otherwise must be going into sea or joining an existing river; code below
        # will handle that automatically
        while curr_loc != start:
            prev_loc = curr_loc
            curr_loc = predecessor[curr_loc]
           
            new_river = river.River()
            # find direction from prev_loc to curr_loc             
            direction = hexgrid.get_direction(curr_loc, prev_loc)
            new_river.set_outflow(direction)
            rivers[curr_loc]= new_river
            if prev_loc in rivers:
                rivers[prev_loc].add_inflow(hexgrid.get_reverse(direction))
        
    
    def gen_rivers(self, elevation):
        catchment = make_2D_list(self.padded_width, self.padded_height, 0)
        rivers = {}
#       
        hex_coords = [Loc(x, y) for x in range(self.padded_width) for y in range(self.padded_height)]
        locations_by_elev = sorted(hex_coords, key=lambda loc: elevation[loc.x][loc.y], reverse=True) 
        
        # initialize rain on higher elevations
        highest_elevs = locations_by_elev[ : int(len(locations_by_elev) * self.RAIN_THRESHOLD)]
        for (x, y) in highest_elevs:
            catchment[x][y] = 1
            
        river_starts = []
        
        # visit locations from highest to lowest, moving rain downhill
        while len(locations_by_elev) > 0:
            curr_loc= locations_by_elev.pop(0)
            local_elev = elevation[curr_loc.x][curr_loc.y]
            local_accum = catchment[curr_loc.x][curr_loc.y]
            
            # don't care what happens to rain once it reaches sea
            if local_elev <= self.sea_level:
                break
            
            neighbors = hexgrid.get_neighbor_coords(curr_loc, self.padded_width, self.padded_height)
            
            # if enough has accumulated to start a river, and there isn't already a river start
            # neighboring this one, begin a new river here.
            if local_accum > self.RIVER_THRESHOLD:
                river_start = True
                for neighbor in neighbors:
                    if neighbor in river_starts:
                        river_start = False
                if river_start:
                    river_starts.append(curr_loc)
            else:
                # if no river started yet, move all water from this loc to lowest neighbor (in some
                # cases the lowest neighbor will actually be up, which will have no effect, since we won't revisit
                # that location.  
                lowest = min(neighbors, key = lambda hex_loc : elevation[hex_loc.x][hex_loc.y]) #
                #self.find_lowest_neighbor(curr_loc, elevation)
                catchment[lowest.x][lowest.y] += local_accum
        
        # lowest locations on edge of map are potential  river end points
        edge_locs = [Loc(x, 0) for x in range(self.padded_width)]
        edge_locs += [Loc(0, y) for y in range(self.padded_height)]
        edge_locs += [Loc(x, self.padded_height - 1) for x in range(self.padded_width)]
        edge_locs += [Loc(self.padded_width - 1, y) for y in range(self.padded_height)]
        edges_by_elev = sorted(edge_locs, key=lambda loc: elevation[loc.x][loc.y]) 
        lowest_edge_elevs = edges_by_elev[ : int(len(edges_by_elev) * self.EDGE_RIVER_END_THRESHOLD)]
        
        # generate rivers
        for start_point in river_starts:
            self.find_river_path(start_point, lowest_edge_elevs, rivers, elevation)
               
        return rivers

    def gen_forests(self, elevation, rivers):
        forests = make_2D_list(self.padded_width, self.padded_height, False)
     
        def forest_seed_function(x, y):
            result = 0
            for y in range(y - self.SEED_SCAN_RNG, y + self.SEED_SCAN_RNG + 1):
                for x in range(x - self.SEED_SCAN_RNG, x + self.SEED_SCAN_RNG + 1):
                    if x < 0 or y < 0 or x >= self.padded_width or y >= self.padded_height:
                        continue
                    if elevation[x][y] > self.mountain_level:
                        result -= 1 / self.SEED_SCAN_RNG ** 2
                    if Loc(x, y) in rivers:
                        result += 1 / self.SEED_SCAN_RNG ** 2
            return result
        
        forest_map = self.gen_heightmap(0.5, forest_seed_function)
        for y in range(self.padded_width):
            for x in range(self.padded_height):
                forests[x][y] = elevation[x][y] > self.sea_level and elevation[x][y] < self.hill_level and forest_map[x][y] > 0
        
        return forests
    
    def gen_terrain(self, elevation, rivers, forests):
        new_map = hexmap.Hexmap(self.width, self.height)
        
        for x in range(self.width):
            for y in range(self.height):
                pad_x, pad_y = x + self.PAD / 2 , y + self.PAD / 2
                height = elevation[pad_x][pad_y]
                
                hex_type = terrain.PLAIN
                if forests[pad_x][pad_y]:
                    hex_type = terrain.FOREST
                if height < self.sea_level:
                    hex_type = terrain.OCEAN
                if height > self.hill_level:
                    hex_type = terrain.HILL
                if height > self.mountain_level:
                    hex_type = terrain.MOUNTAIN
                
                if Loc(pad_x, pad_y) in rivers:
                    river = rivers[Loc(pad_x, pad_y)]
                else:
                    river = None                         
                new_map.set_hex(x, y,  hexmap.Hex(x, y, hex_type, river, height))   
        return new_map
    
    def generate(self):
        elevation = self.gen_heightmap(0.95)  
        elevation = self.erode_heightmap(elevation, 5)           
        rivers = self.gen_rivers(elevation)
        forests = self.gen_forests(elevation, rivers)
        new_map = self.gen_terrain(elevation, rivers, forests)
 
        return new_map

