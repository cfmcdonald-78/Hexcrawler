'''
Created on Jul 9, 2012

@author: Chris
'''
import collections 
import  hexgrid
from math import sqrt, ceil
import random
from util.tools import BIGNUM

SiteParams = collections.namedtuple('SiteParams', ['site_type', 'frequency', 'min_level', 'max_level'])
Substitution = collections.namedtuple('Substitution', ['sub_for', 'frequency', 'function', 'params', 'terrain'])
TerrainSub = collections.namedtuple('TerrainSub', ['new_terrain', 'function', 'params'])

### ZONE SUBSTITUTION FUNCTIONS ###
# Used to measure the suitability of a given candidate zone for being replaced with a substitution zone

# sum -distances from candidate zone to all zones of types listed in param_list
def min_total_distance(candidate_zone, hex_map, desirable_zone_types):
    return -max_total_distance(candidate_zone, hex_map, desirable_zone_types)

# sum distances from candidate zone to all zones of types listed in param_list
def max_total_distance(candidate_zone, hex_map, undesirable_zone_types):
    total_distance = 0
    
    candidate_x, candidate_y = candidate_zone.center
#    candidate_y = candidate_zone.y
    print "candidate zone at " + str(candidate_x) + "," + str(candidate_y)
    
    for zone in hex_map.get_zones():
        if zone != candidate_zone and zone.get_type().name in undesirable_zone_types:
#            print zone.get_type().name + " at " + str(zone.bounds.x) + "," + str(zone.bounds.y)
            zone_x, zone_y = zone.center
            x_dist = zone_x - candidate_x
            y_dist = zone_y - candidate_y
            total_distance +=  sqrt(x_dist ** 2 + y_dist ** 2) 
            
#    print "total distance to desired/undesired from " + str(candidate_zone.bounds) + "is " + str(total_distance)
    return total_distance

# maximizes distance to closest undesireable zone
def max_proximity(candidate_zone, hex_map, undesirable_zone_types):
    candidate_x = candidate_zone.center.x
    candidate_y = candidate_zone.center.y
    
    print "candidate zone of type " + candidate_zone.get_type().name + " at " + str(candidate_x) + "," + str(candidate_y)
    
    min_distance = BIGNUM
    for zone in hex_map.get_zones():
        if zone != candidate_zone and zone.get_type().name in undesirable_zone_types:
#            zone_x, zone_y = zone.center
#            x_dist = zone_x - candidate_x
#            y_dist = zone_y - candidate_y
            dist_to_undesirable = hexgrid.get_distance(zone.center, candidate_zone.center)
            print "undesirable zone of type " + zone.get_type().name + " at " + str(zone.center.x) + "," + str(zone.center.y) + ". distance to candidate: " + str(dist_to_undesirable)
            min_distance = min(min_distance, dist_to_undesirable)

    print "min distance to undesirable: " + str(min_distance)
    return min_distance

# minimizes amount of given terrain types
def min_terrain(candidate_zone, hex_map, undesirable_terrain_types):
    return -max_terrain(candidate_zone, hex_map, undesirable_terrain_types)
   
   # minimizes amount of given terrain types 
def max_terrain(candidate_zone, hex_map, desirable_terrain_types):
    
    terrain_count = 0
    zone_size = len(candidate_zone.hex_locs)
    for hex_loc in candidate_zone.hex_locs:
        curr_hex = hex_map.get_hex(hex_loc.x, hex_loc.y)
        if curr_hex.hex_type in desirable_terrain_types:
            terrain_count += 1
        if curr_hex.has_river() and "River" in desirable_terrain_types:
            
            terrain_count += 1
            
    # TODO: make option to ignore oceans in scaling the count?  Right now
    # this tends to always put desolation on high seas, since that's where fewest rivers are, haha.
    return ( terrain_count / float(zone_size) )
    
    

zone_sub_functions = {"min_total_distance": min_total_distance, "max_total_distance": max_total_distance,
                      "max_proximity": max_proximity, "min_terrain": min_terrain, "max_terrain": max_terrain}

### TERRAIN SUBSTITUTION FUNCTIONS ###
# Used to decide how to replace one kind of terrain with another in a substitution zone

# pick a random # of the candidate locations, based on frequency passed into param list
def scatter(candidate_locations, param_list):
    frequency = param_list[0]
    num_to_sub = int( ceil(len(candidate_locations) * frequency) )
    random.shuffle(candidate_locations)
    
    changed_locations = []
    for i in range(num_to_sub):
        changed_locations.append(candidate_locations[i])
    return changed_locations

terrain_sub_functions = {"scatter": scatter}

zone_types = []
type_adjectives = {}

class ZoneType(object):
    '''
    classdocs
    '''

    def __init__(self, name, terrain_weight, substitution_info, min_fraction, site_param_list):
        '''
        Constructor
        '''
        self.name = name
        self.substitution_info = substitution_info
        self.terrain_weight = terrain_weight
        self.min_fraction = min_fraction
        self.site_param_list = site_param_list
    
    def hex_weight(self, curr_hex):
        weight = 0
        if curr_hex.hex_type.name in self.terrain_weight:
            weight += self.terrain_weight[curr_hex.hex_type.name] 
        if curr_hex.has_river() and "River" in self.terrain_weight:
            weight += self.terrain_weight["River"]
        
        return weight
    
    def compute_terrain_weight(self, hex_map, hex_locs):
        total_size = len(hex_locs) #bounds.width * bounds.height
        
        weight = 0
#        for y in range (bounds.y, bounds.y + bounds.height):
#            for x in range(bounds.x, bounds.x + bounds.width):
        for x, y in hex_locs:
            curr_hex = hex_map.get_hex(x, y)
            weight += self.hex_weight(curr_hex)
                
        return weight / float(total_size)