'''
Created on Jun 28, 2012

@author: Chris
'''
import random, math
import site_type, site, terrain, zone_type
from util.tools import Loc
import hexgrid

used_zone_names = {}

def compute_num_sites(land_hexes, site_frequency):
    scale_factor = land_hexes / 100.0
    min = math.ceil(site_frequency[0] * scale_factor)
    max = math.ceil(site_frequency[1] * scale_factor) if len(site_frequency) > 1 else min
    
    if site_frequency[0] < 1 and random.random() >= (site_frequency[0] * scale_factor):
            return 0
        
    return random.randint(min, max) 
#def scaled_random_range(size, min_chance, max_chance):
#    return random.randint(int(math.ceil(size * min_chance)), int(math.ceil(size * max_chance)))



STORMY = "Stormy"
FLOODED = "Flooded"

class Zone(object):
    
    def __init__(self, type, x, y, hex_locs):
#        self.bounds = bounds
        self.hex_locs = hex_locs
#        self.x = x
#        self.y = y
        self.center = Loc(x, y)
        self.zone_type = type
        self.site_count = {}
        self.traits = {}
        self.name = "None"
        
    def __str__(self):
        return self.name + "(" + self.zone_type.name + ")"
    
    def assign_sites(self, hex_map, site_type, sites_to_assign, min_level, max_level, locs_available, npc_table):
   
        assignments = 0
        
        if site_type.zone_centered:
            locs_available.sort(key = lambda hex_loc : -hexgrid.get_distance(hex_loc, self.center))  # prefer valid locations closest to center of zone
        else:
            random.shuffle(locs_available)  # randomize valid  locations
         
        # examine valid locations until we find one that doesn't already have a site or a neighboring site
        while len(locs_available) > 0 and assignments < sites_to_assign:
            loc = locs_available.pop()
            assigned_hex = hex_map.get_hex(loc.x, loc.y)
            neighbors_with_sites = len([neighbor for neighbor in hex_map.get_neighbors(loc.x, loc.y) if neighbor.site != None])
                
            # only actually assign site if hex is legal terrain without existing site and neighbors don't have sites
            if assigned_hex.site == None and neighbors_with_sites == 0:
                level = random.randint(min_level, max_level)
                assigned_hex.site = site.Site(assigned_hex, site_type, level, npc_table[site_type.owner_name]) 
                assignments += 1
        
        return assignments
    
    def get_type(self):
        return self.zone_type

    def get_name(self):
        return self.name
    
    def trait_value(self, trait):
        return self.traits.get(trait, 0)

    def change_type(self, new_type):
        assert(len(self.site_count.keys()) == 0) # can't reassign type once zone has been populated
        self.zone_type = new_type
        
    def gen_name(self):
        
        while True:
            noun = random.choice(terrain.terrain_nouns[self.predominant_terrain])
            adjective = random.choice(zone_type.type_adjectives[self.zone_type.name])
            new_name = "The " + adjective + " " + noun
            if new_name not in used_zone_names:
                break
            
        used_zone_names[new_name] = True
        self.name = new_name
        
    def set_trait(self, trait, value):
        self.traits[trait] = value
    
    def remove_trait(self, trait):
        del self.traits[trait]
    
    def has_trait(self, trait):
        return trait in self.traits
    
    def is_wild(self):
        return self.zone_type.is_wild()

     
    def populate(self, hex_map, npc_table):
#        total_size =  len(self.hex_locs) #self.bounds.width * self.bounds.height
    
        for count_site_type in site_type.site_types.values():
            self.site_count[count_site_type] = 0
        
        # generate table mapping terrain type to locations of that type in this zone
        terrain_to_locs = {}
        for hex_type in terrain.hex_types:
            terrain_to_locs[hex_type] = []
            
#        for x in range(self.bounds.x, self.bounds.x + self.bounds.width):
#            for y in range(self.bounds.y, self.bounds.y + self.bounds.height):
        for hex_loc in self.hex_locs:
            hex_type = hex_map.get_hex(hex_loc.x, hex_loc.y).hex_type
            terrain_to_locs[hex_type].append(hex_loc)
        
        #do terrain replacement if applicable
        sub_info = self.zone_type.substitution_info
        if sub_info != None:
            terrain_sub_info = sub_info.terrain
            for terrain_name in terrain_sub_info:
                old_terrain_type = terrain.name_to_type[terrain_name]
                terrain_swap_info = terrain_sub_info[terrain_name]
                function = zone_type.terrain_sub_functions[terrain_swap_info["function"]]
                params = terrain_swap_info["params"]
                new_terrain_type = terrain.name_to_type[terrain_swap_info["new_terrain"]]
                changed_locs = function(terrain_to_locs[old_terrain_type], params)
                
                for loc in changed_locs:
                    hex_map.get_hex(loc.x, loc.y).hex_type = new_terrain_type
                    hex_map.get_hex(loc.x, loc.y).original_type = new_terrain_type
                    terrain_to_locs[old_terrain_type].remove(loc)
                    terrain_to_locs[new_terrain_type].append(loc)
    
        self.predominant_terrain= max(terrain_to_locs.keys(), key = lambda hex_type : len(terrain_to_locs[hex_type]))
        self.gen_name()
                  
        # sort site types from most to least restrictive in placement before assigning sites to locations
        locs_avail_table = {}
        for site_params in self.zone_type.site_param_list:  
            locs_avail = []
            for hex_type_name in site_params.site_type.legal_terrain:
                locs_avail += terrain_to_locs.get(terrain.name_to_type[hex_type_name], [])
            #print site_params
            locs_avail_table[site_params.site_type] = locs_avail
    
        self.zone_type.site_param_list.sort(key = lambda site_param : locs_avail_table[site_params.site_type])
    
#        print self.zone_type.name + str(self.bounds)
        land_hexes = len([hex_loc for hex_loc in self.hex_locs if not hex_map.get_hex(hex_loc.x, hex_loc.y).hex_type.is_water()])
        for site_params in self.zone_type.site_param_list:
            num_sites = compute_num_sites(land_hexes, site_params.frequency)
            num_assigned = self.assign_sites(hex_map, site_params.site_type, num_sites, 
                                        site_params.min_level, site_params.max_level, locs_avail_table[site_params.site_type], npc_table)
            if num_assigned < num_sites:
                print "Alert: " + self.get_name() + " wanted " + str(num_sites) + " " + site_params.site_type.name + "s, got " + str(num_assigned)
        
       