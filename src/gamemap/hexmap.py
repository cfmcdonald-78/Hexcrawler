from util.tools import *
#from util.linked_list import LinkedQueue
#from threading import Lock
import random
import zone, terrain, hexgrid, road
import mob.group
import mob.unit as unit, mob.trait as trait, mob.move_mode as move_mode
import hexcrawl.random_event as random_event
import zone_type, site_type
from math import ceil, sqrt
from site import Site

'''
Created on Jun 6, 2012

@author: Chris
'''
FIRE = "fire"


class Hex(object):

    def __init__(self, x, y, hex_type, river_path, height): # possible features: river, keep, city-state, lair, dungeon
        self.x = x
        self.y = y
        self.hex_type = hex_type
        self.original_type = hex_type
        self.river = river_path
        self.road = None
        self.height = height
        self.site = None
        self.active_group = None  # active units/characters in this hex
        self.garrison = None
        self.zone = None
#        self.hidden_group = None
        
        self.storm_duration = 0
        self.storm_penalty = 0
        self.fire_duration = 0
        self.zone_borders = []

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def is_haven(self):
        return self.has_site() and self.site.is_haven()
    
    def set_fire(self, days):
        if self.fire_duration == 0:
            self.fire_duration = days
    
    def has_fire(self):
        return self.fire_duration > 0
    
    def update_fire_state(self):
        if self.has_fire():
            self.fire_duration -= 1
    
    def has_storm(self):
        return self.storm_duration > 0
    
    def has_water(self):
        return self.has_river() or self.hex_type.is_water()
    
    def set_storm(self, days, severity):
        self.storm_penalty = severity
        self.storm_duration = days

    def get_storm_penalty(self):
        return self.storm_penalty
    
    def update_storm_state(self):
        if self.has_storm():
            self.storm_duration -= 1
            if self.storm_duration == 0:
                self.storm_penalty = 0
    
    def set_site(self, site):
        self.site = site
        
    def get_visibility(self, x, y):
        return self.mask.get_visibility(x, y)
    
    def has_occupants(self):
        return self.active_group != None or self.garrison != None
    
    def has_friendlies(self, group):
        # TODO: race condition!! MoveProcess running on main thread is modifying active groups while this code is reading them from AI thread
        if self.active_group != None and self.active_group.owner == group.owner:
            return True
        if self.garrison != None and self.garrison.owner == group.owner:
            return True
        return False
    
    # returns true if group can't move through this space without either merging or fighting
    def is_blocked(self, group):
        if self.active_group != None:
            return self.active_group != group
        if self.garrison != None and self.site.is_hostile(group.get_owner()): #and self.site.is_hostile(group):
            return True
        return False

    # determine if this is a place where a move will cause a battle
    # if there's an active group, fight will happen unless both groups belong to same player
    # if there's a garrisoned site, it will only fight if it considers the incoming unit hostile   
    def will_fight(self, active_player):
        if self.active_group != None and active_player != self.active_group.get_owner(): #   player_type.is_hostile(group,  self.active_group.get_owner() != group.get_owner():
            return True
        if self.garrison != None and self.site.is_hostile(active_player): #and self.site.is_hostile(group):
            return True
        return False
    
    def heals_unit(self):
        # heal at any active site
        return self.has_site() and self.site.is_active()
    
    def is_settled(self):
        return self.hex_type.is_settled()
    
    def can_be_settled(self):
        return self.hex_type.name in terrain.settle_map
    
    def pillage(self):
        if self.hex_type.name in terrain.pillage_map:
            self.hex_type = terrain.name_to_type[terrain.pillage_map[self.hex_type.name]]
            
    def settle(self, neighbors):
        if self.hex_type.name in terrain.settle_map:
            # can't settle where there are pillager afoot
            if self.active_group != None and self.active_group.has_trait(trait.PILLAGER):
                return False
            
            for neighbor in neighbors:
                # can't settle adjacent to pillaging sites
                if neighbor.has_site() and neighbor.site.pillages():
                    return False
            self.hex_type = terrain.name_to_type[terrain.settle_map[self.hex_type.name]]
            
    def has_site(self):
        return self.site != None
    
    def has_lootable_site(self, group):
        if self.site != None:
            return self.site.is_lootable(group)
        return False
    
    def remove_site(self, site):
        assert(site == self.site)
        self.site = None
    
    def set_road(self, road):
        self.road = road
    
    def has_river(self):
        return self.river != None
    
    def has_garrison(self):
        return self.garrison != None
    
    def get_garrison(self):
        return self.garrison
    
    def deep_garrison(self):
        return self.site != None and self.site.garrison_depth() > 1
    
    def get_active_group(self):
        return self.active_group
      
    def get_defenders(self):
        if self.active_group != None:
            return self.active_group
        return self.garrison
    
    def spy_on(self):
        if self.active_group != None:
            self.active_group.reveal()
    
    def armies_can_fight(self):
        if self.active_group == None and self.has_site():
            return not self.site.is_tight_quarters()
        return True
    
    def remove_group(self, group):
        if self.garrison == group:
            self.garrison = None
            return
        if self.active_group == group:
            self.active_group = None
            return
        
        raise ValueError("attempted to remove group from hex where it wasn't present")

    def add_garrison(self, group):
        assert(self.garrison == None)
        self.garrison = group
        self.garrison.set_hex(self)
        
    def add_group(self, group):
        # BUG_FINDING_CODE
       
        if isinstance(group, mob.group.ZonePatrol):
            if group.get_site().get_hex().zone != self.zone:
                assert(False)
#                print group
#                print "Moved into: " + str(self.zone)
#                print "Home zone: " + str(group.get_site().get_hex().zone)

        # /BUG_FINDING_CODE
        
#        assert(group.num_units() > 0)
        if self.active_group != None:
            self.active_group.merge(group)
        else:
            self.active_group = group
            self.active_group.set_hex(self)
   
    def legal_move(self, group):
        # make sure group can legally enter terrain
        if not terrain.is_legal_terrain(self.hex_type, group):
            return False
        
        if isinstance(group, mob.group.ZonePatrol) and self.zone != group.get_zone():
            # patrols can't leave their zone of origin
            return False
        
        if self.active_group != None and self.active_group.get_owner() != group.get_owner() and self.active_group.is_hidden():
            # 'hidden' group prevents movement, so you'll know it's there.  But alternative is to have 2 groups sharing
            # a space, which creates beaucoup problems. 
            return False
        
        # can only move into a space with an active group that you can't fight if you can legally merge
        if self.active_group != None and not self.will_fight(group.get_owner()): 
            return self.active_group.can_merge(group) 
        
        # can't enter a haven if someone else is there or ever if you aren't an actor
#        if self.is_haven():
#            if not group.get_owner().is_actor():
#                return False
#            
#            if self.active_group != None:
#                return self.active_group.can_merge(group)
#            
#            return self.garrison == None or self.garrison.get_owner() == group.get_owner()

        return True
    
    # get cost of moving from this hex to an adjacent hex
    def get_move_cost(self, move_group, adjacent):
        storm_penalty = (1 if self.has_storm() else 0) # storms add 1 to cost of each hex
        
        if move_group.get_move_mode() == move_mode.FLIGHT:
            return terrain.BASE_MOVE_COST + storm_penalty
        
        if self.river != None and not self.river.is_flooded:
            direction = hexgrid.get_direction(self, adjacent)
            if direction == self.river.out_flow or direction in self.river.in_flows:
                return terrain.BASE_MOVE_COST + storm_penalty
        if self.road != None:
            direction = hexgrid.get_direction(self, adjacent)
            if direction in self.road.connections:
                return terrain.BASE_MOVE_COST + storm_penalty
        
        hex_cost = adjacent.hex_type.move_cost 
        if  adjacent.hex_type.is_water():
            hex_cost = int (hex_cost * move_group.get_highest_trait(trait.NAVAL))
        
        return hex_cost + storm_penalty

    def add_zone_border(self, neighbor):
        self.zone_borders.append(hexgrid.get_direction(self, neighbor))
        
    def get_zone_borders(self):
        return self.zone_borders

    def set_zone(self, zone_set):
        self.zone = zone_set
        
    def get_zone(self):
        return self.zone

class Hexmap:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.zones = []
     
        self.zone_width = 9
        self.zone_height = 9
        
        # generate empty hexmap
        self.hexes = make_2D_list(self.width, self.height)
    
#    def initialize(self, is_new_game):
#        event_manager.add_listener(self.handle_event, event_manager.DAY_START)
    
    def start_day(self, turn):
#        if event.type == event_manager.DAY_END:
        self.do_regrowth()
        self.update_disasters()
        if turn.at_week_start():
            # recompute road net at start of week
            road.build_road_net(self)
       
#            for zone in self.zones:
#                zone.update_storm()
    
    # tell rivers that a day has passed and floods should subside accordingly
    # tell hexes that day has passed and storms should subside accordingly
    def update_disasters(self):
        new_fires = []
        for y in range(self.height):
            for x in range(self.width):
                curr_hex = self.get_hex(x, y)
                if curr_hex.has_river():
                    curr_hex.river.update_flood_state()
                curr_hex.update_storm_state()
                
                if curr_hex.has_fire():
                    # spread fire
                    neighbors = self.get_neighbors(curr_hex.x, curr_hex.y)
                    for neighbor in neighbors:
                        if random.random() <= random_event.FIRE_SPREAD_CHANCE:
                            new_fires.append(neighbor)
                           
                    curr_hex.update_fire_state()
                    if not curr_hex.has_fire():
                        # burned out
                        curr_hex.hex_type = terrain.SCORCHED
        for fire_hex in new_fires:
            if fire_hex.hex_type.is_forest():
                fire_hex.set_fire(random.randint( random_event.MIN_FIRE_DURATION, random_event.MAX_FIRE_DURATION))
                        

    # some terrain that is leveled by settling can grow back if it is cleared of settlement
    def do_regrowth(self):
        regrow_map = make_2D_list(self.width, self.height, init_value=False)
        
        for y in range(self.height):
            for x in range(self.width):
                curr_hex = self.get_hex(x, y)
                regrowth_chance = curr_hex.original_type.regrowth_chance
                if (curr_hex.is_settled() or regrowth_chance == 0.0 or 
                    curr_hex.hex_type.name == curr_hex.original_type.name):
                    continue
                
                # have a regrowable hex, check adjacent to determine total regrowth_chance
                total_chance = regrowth_chance
                neighbors = self.get_neighbors(x, y)
                for neighbor in neighbors:
                    if neighbor.hex_type.name == curr_hex.original_type.name:
                        total_chance += regrowth_chance
                
                if random.random() <= total_chance:
                    regrow_map[x][y] = True
        
        for y in range(self.height):
            for x in range(self.width):
                if regrow_map[x][y]:
                    curr_hex = self.get_hex(x, y)
                    curr_hex.hex_type = terrain.name_to_type[curr_hex.original_type.name]

    def create_zone(self, assigned_type, zone_center, zone_points, zones_by_type):
        new_zone = zone.Zone(assigned_type, zone_center.x, zone_center.y, zone_points)
        for loc in zone_points:
            self.zone_map[(loc.x, loc.y)] = new_zone
            
        zones_by_type[assigned_type.name].append(new_zone)
            
        self.zones.append(new_zone)

    # returns true if map successfully populated with zones , false if this map fell outside allowable
    # parameters
    def assign_zones(self):
        self.zone_map = {}
        zones_across, zones_high = int (ceil(self.width / self.zone_width)), int(ceil(self.height / self.zone_height))
        #frontier_map = make_2D_list(zones_across, zones_high)
        
        zones_by_type = {}
        for curr_type in zone_type.zone_types:
            zones_by_type[curr_type.name] = []
    
        # generate voronoi diagram of zones
        zone_centers = []
        zone_points = {}
        for zone_y in range(zones_high):
            for zone_x in range(zones_across):
                center_x = zone_x * self.zone_width + (self.zone_width/4) + random.randint(0, self.zone_width/2)
                center_y = zone_y * self.zone_height + (self.zone_height/4) + random.randint(0, self.zone_height/2)
                new_center = Loc(center_x, center_y)
                zone_centers.append(new_center)
                zone_points[new_center] = []
                
        # assign each point of hex map to a voronoi cell.  Determine 
        for y in range(self.height):
            for x in range(self.width):
                closest_center = min(zone_centers, key = lambda curr_center : sqrt( (curr_center.x - x) ** 2 + (curr_center.y - y) ** 2))
                zone_points[closest_center].append(Loc(x, y))
        
        print "Total zones: " + str(len(zone_centers))  
        # assign partition zone types to any zone that has a positive terrain weight for
        # a partition type
        partition_zone_types = [curr_type for curr_type in zone_type.zone_types if curr_type.type == zone_type.PARTITION]
        
        i = 0
        while i < len(zone_centers):
            zone_center = zone_centers[i]
            weight, best_type = max([(curr_type.compute_terrain_weight(self, zone_points[zone_center]), 
                                      curr_type) for curr_type in partition_zone_types])
            if weight > 0:
                self.create_zone(best_type, zone_center, zone_points[zone_center], zones_by_type)
                zone_centers.remove(zone_center)
                print "adding partition zone centered on " + str(zone_center)
            else:
                i += 1
            
        
        if len(zone_centers) < 0.5 * zones_across * zones_high:
            print "rejected map, not enough space left for basic zones after allocating partitions"
            return False
        
        # assign base zone types to remaining zones, in desired proportions.
        base_zone_types = [curr_type for curr_type in zone_type.zone_types if curr_type.type == zone_type.BASE]
        #random.shuffle(base_zone_types)
       
        # random initial assignments
        FRAC_INCS = 1000
        fractions = {}
        for curr_type in base_zone_types:
            fractions[curr_type] = (curr_type.min_fraction + (curr_type.max_fraction- curr_type.min_fraction) * random.randint(0, FRAC_INCS)) 
        total_frac = sum(fractions.itervalues())
        
        # randomly add or remove fractional increments until sum is 1
        while total_frac > FRAC_INCS:
            rand_type = random.choice(base_zone_types)
            if rand_type.min_fraction * FRAC_INCS < fractions[rand_type]:
                fractions[rand_type] -= 1
                total_frac -= 1
        while total_frac < FRAC_INCS:
            rand_type = random.choice(base_zone_types)
            if rand_type.max_fraction * FRAC_INCS > fractions[rand_type]:
                fractions[rand_type] += 1
                total_frac += 1
        
        num_zones = {}
        zones_to_allocate = len(zone_centers)
        zones_left = zones_to_allocate
        for i in range(len(base_zone_types) - 1):
            curr_type = base_zone_types[i]
            num_zones[curr_type] = int(round((fractions[curr_type] / float(FRAC_INCS)) * zones_to_allocate))
            zones_left -= num_zones[curr_type]
        num_zones[base_zone_types[-1]] = zones_left
        
        # allocate zones greedily by weight
        zone_matches = [(zone_center, curr_type) for curr_type in base_zone_types for zone_center in zone_centers]
        zone_matches.sort(key = lambda match : match[1].compute_terrain_weight(self, zone_points[match[0]]))
        
        allocated = 0
        center_allocated = set([])
        while allocated < zones_to_allocate:
            zone_center, curr_type = zone_matches.pop()
            print curr_type.compute_terrain_weight(self, zone_points[zone_center])
            if num_zones[curr_type] > 0 and zone_center not in center_allocated:
                self.create_zone(curr_type, zone_center, zone_points[zone_center], zones_by_type)
                num_zones[curr_type] -= 1
                center_allocated.add(zone_center)
                allocated += 1
            
        # do zone substitutions
        sub_zone_types = [curr_type for curr_type in zone_type.zone_types if curr_type.substitution_info != None]
        for sub_zone_type in sub_zone_types:
                sub_info = sub_zone_type.substitution_info
                sub_candidates = zones_by_type[sub_info.sub_for]
                
                # figure out how many zones to replace (R), sort the replacement candidates by the substitution function,
                # and then switch the best R candidates from the previous zone type to the new one
                num_to_sub = int( ceil(sub_info.frequency * len(sub_candidates)) )
                sub_function = zone_type.zone_sub_functions[sub_info.function]
                sub_candidates.sort(key = lambda candidate : sub_function(candidate, self, sub_info.params))
#                print "top candidate at: " + str(sub_candidates[-1].bounds.x)  + "," + str(sub_candidates[-1].bounds.y)
                for i in range(num_to_sub):
                    reassigned_zone = sub_candidates.pop()
                    reassigned_zone.change_type(sub_zone_type)
                    if sub_zone_type.name == "Borderland":
                        assert(num_to_sub == 1)
                        self.start_zone = reassigned_zone  
                        
        # ensure start zone has at least 1 frontier neighbor to cushion start
        start_zone_neighbors = set([])
        for zone_loc in self.start_zone.hex_locs:
            neighbor_hexes = self.get_neighbors(zone_loc.x, zone_loc.y)
            for neighbor_hex in neighbor_hexes:
                    neighbor_zone = self.zone_map[(neighbor_hex.x, neighbor_hex.y)]
                    if neighbor_zone != self.start_zone:
                        start_zone_neighbors.add(neighbor_zone)
        
        if not any([neighbor.get_type().name == "Frontier" for neighbor in start_zone_neighbors]):
            print "rejected map, no frontier zone adjacent to start zone"
            return False

        # find and mark zones and borders between zones
        for y in range(self.height):
            for x in range(self.width):
                curr_hex = self.get_hex(x, y)
                curr_hex.set_zone(self.zone_map[(x, y)])
                up_left_neighbors = [neighbor for neighbor in self.get_neighbors(x, y) if hexgrid.get_direction(curr_hex, neighbor) < 3]
                for neighbor in up_left_neighbors:
                    if self.zone_map[(x, y)] != self.zone_map[(neighbor.x, neighbor.y)]:
                        curr_hex.add_zone_border(neighbor)       

        zone_count = {}
        for curr_type in zone_type.zone_types:
            zone_count[curr_type] = 0
        for curr_zone in self.zones:   
            zone_count[curr_zone.get_type() ] += 1 
        for curr_type in zone_count:
            print curr_type.name + ": " + str(zone_count[curr_type])
    
        return True

    def populate(self, npc_table):
        for curr_zone in self.zones:
            curr_zone.populate(self, npc_table)
        
        # place global types
        #global_site_types = [curr_type for curr_type in site_type.site_types if curr_type.is_global()]
        #for global_site_type in [curr_type for curr_type in site_type.site_types if curr_type.is_global()]:
        site_type.do_global_allocation(self)
        
        for curr_site in self.get_sites():
            curr_site.initialize()
         # for i in range(MIN_HERO_LAIR_LEVEL, MAX_HERO_LAIR_LEVEL + 1):
   #     lair_candidates = hex_map.find_site("Lair", level_range = (i, i), find_all = True)
   #     if len(lair_candidates) == 0:
   #         continue
        
   #     chosen_lair = random.choice(lair_candidates)
   #     chosen_lair.set_prisoner(hero.Hero(unit.random_hero_type()))
        
  
    def get_start_zone(self):
        return self.start_zone
    
    def get_zones(self):
        return self.zones
    
    def get_neighbors(self, x, y):
        # TODO: fix this so it doeesn't double-check the coordinates (once in get_neighbor coords, once in get_hex!
        return [self.get_hex(new_x, new_y) for (new_x, new_y) in hexgrid.get_neighbor_coords(Loc(x, y), self.width, self.height)]
    
    def get_spawn_hex(self, center_hex):
        if center_hex.active_group == None:
            return center_hex
        # can't spawn if there's already someone there or if you are crossing a zone boundary
        valid_neighbors = [neighbor for neighbor in self.get_neighbors(center_hex.x, center_hex.y) if (neighbor.active_group == None
                           and neighbor.get_zone() == center_hex.get_zone())]
        if len(valid_neighbors) == 0:
            return None
        
        return random.choice(valid_neighbors)
    
    def set_hex(self, x, y, map_hex):
        if self.hexes[x][y] != None:
            "reset existing hex!"
            
        if not isinstance(map_hex, Hex):
            raise TypeError("attempted to assign non-hex object to hex")
            
        self.hexes[x][y] = map_hex
       
    def get_hex(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        
        return self.hexes[x][y]  
#
    def get_zone(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        return self.zone_map[(x, y)]
    
    def get_legal_moves_from(self, hex_x, hex_y, active_player):
        start_hex = self.get_hex(hex_x, hex_y)
        if start_hex == None or start_hex.active_group == None:
            return []
        
        active_group = start_hex.active_group
        
        max_move = (active_group.get_moves_left() if active_group.get_owner() == active_player 
                    else active_group.get_max_moves())
        
        def neighbor_func(curr_hex):
            if curr_hex.is_blocked(active_group):
                # can't move through a hex with other forces
                return []
            return self.get_neighbors(curr_hex.x, curr_hex.y)
        def cost_func(curr_hex, new_hex):
            if not new_hex.legal_move(active_group):
                return BIGNUM
            return curr_hex.get_move_cost(active_group, new_hex)
        
        return breadth_first_search(start_hex, max_move, neighbor_func, cost_func, exclude_start = True)
        # breadth-first search
        
    
    #  breadth-first search
    def get_hexes_in_radius(self, center_hex, radius, blocking_terrain = []):
#        def neighbor_func(curr_hex):
#            return self.get_neighbors(curr_hex.x, curr_hex.y)
#        def cost_func(curr_hex, new_hex):
#            return BIGNUM if (new_hex.hex_type.name in blocking_terrain) else 1
#        
#        return breadth_first_search(center_hex, radius, neighbor_func, cost_func)
        
        to_visit = deque()
        to_visit.appendleft((0, center_hex))
        visited = set([])
        while len(to_visit) > 0:
            distance, visit_hex = to_visit.pop()
            if distance < radius:
                neighbors = [neighbor for neighbor in self.get_neighbors(visit_hex.x, visit_hex.y) if (neighbor not in visited and
                                    neighbor.hex_type not in blocking_terrain)]
                for neighbor in neighbors:
                    to_visit.appendleft((distance + 1, neighbor))
            visited.add(visit_hex)
        return visited
    
    def pillage(self, center_hex, radius):
        pillage_hexes = self.get_hexes_in_radius(center_hex, radius)
        for curr_hex in pillage_hexes:
            curr_hex.pillage()
    
    # Spread settlement one ring at a time, out to radius.  Only spread to next ring if all possible hexes in 
    # previous rings are already full.  The expansion of settlement cannot cross mountains - this prevents
    # a weird quirk where sites hemmed in by mountains get to skip rings and expand very quickly.
    def spread_settlement(self, center_hex, radius):
        settle_hexes = self.get_hexes_in_radius(center_hex, radius, ["Mountain"])
        distances = {}
        for curr_hex in settle_hexes:
            distances[curr_hex] = hexgrid.get_distance(center_hex, curr_hex)
        hexes_by_radius = sorted(settle_hexes, key = lambda curr_hex : distances[curr_hex])
      
        # spread out until we find an unsettled settleable hex.  Will then attemp to settle
        # every hex in the same ring.  Can't spread to a new ring until succesfully filled in
        # all settleable hexes in previous ring (and held on to them through next settlement cycle)
        settled_radius = radius
        for curr_hex in hexes_by_radius:
        
            if distances[curr_hex] > settled_radius:
                break
            
            if curr_hex.can_be_settled() and not curr_hex.is_settled():
                settled_radius = distances[curr_hex]
                curr_hex.settle(self.get_neighbors(curr_hex.x, curr_hex.y))
      
    def count_settled_hexes(self, center_hex, radius):
        hexes_in_range = self.get_hexes_in_radius(center_hex, radius)
        
        # count settled hexes and return result
        count = 0
        for curr_hex in hexes_in_range:
            if curr_hex.is_settled():
                count += 1
        return count
    
    def place_site(self, new_site_type, level, player_table, required_zone_types=None):
        def is_valid_site_hex(curr_hex):
            if curr_hex.active_group != None:
                return False
        
            if curr_hex.hex_type.name not in new_site_type.legal_terrain:
                return False
        
            if curr_hex.has_site():
                return False
        
            if required_zone_types != None and self.get_zone(curr_hex.x, curr_hex.y).zone_type.name not in required_zone_types:
                return False 
        
            neighbors = self.get_neighbors(curr_hex.x, curr_hex.y)
        
            return not any([neighbor.has_site() for neighbor in neighbors])
    
        site_hex = self.get_random_hex(is_valid_site_hex)
        if site_hex == None:
            return None
    
        site_hex.site = Site(site_hex, new_site_type, level, player_table[new_site_type.owner_name])
        site_hex.site.initialize()
        return site_hex
    
    
    def get_sites(self, filter_func = lambda curr_site : True):
        results = []
    
        for y in range(self.height):
                for x in range(self.width):
                    curr_site = self.hexes[x][y].site
                    if curr_site != None and filter_func(curr_site):
                        results.append(curr_site)
        return results
    
    # find a site of given type on the map, optionally constrained by level range
    # and a particular map zone, and active status.  Optionally can find list of all such sites
    def find_site(self, target_type_name, level_range = None, search_zone = None, must_be_active = True, find_all=False):
        results = [] if find_all else None
        
        def check_hex(x, y, ):
            curr_site = self.hexes[x][y].site
            if curr_site != None and curr_site.site_type.name == target_type_name and (curr_site.is_active() or not must_be_active):
                level = curr_site.level
                if level_range == None or (level_range[0] <= level and level <= level_range[1]):
                    if find_all:
                        results.append(curr_site)
                        return None
                    else:
                        return curr_site
        
        if search_zone != None:
            for x, y in search_zone.hex_locs:
                found = check_hex(x, y)
                if found != None:
                    return found
        else:
            for y in range(self.height):
                for x in range(self.width):
                    found = check_hex(x, y)
                    if found != None:
                        return found
       
        return results
    
    def get_random_hex(self, condition_func):
        # find all hexes that satisfy condition function
        matches = []
        for y in range(self.height):
            for x in range(self.width):
                curr_hex = self.get_hex(x, y)
                if condition_func(curr_hex):
                    matches.append(curr_hex)
        
        if len(matches) > 0:
            return random.choice(matches)
        return None
    
    def get_random_zone(self):
        return random.choice(self.zones)