'''
Created on Apr 24, 2013

@author: Chris
'''
import group, unit, trait, hexcrawl.player_type as player_type
import random

HORDE_RANGE = 3
HORDE_AGGRESSION = 3
HORDE_DELAY_BY_LEVEL = [3, 8, 14, 20, 24, 28, 32, 38]

horde_types_by_name = {}

class HordeType(object):
    
    def __init__(self, name, leader_name, level, unit_name_list):
        self.name = name
        self.leader_name = leader_name
        self.level = level
        self.unit_type_names = unit_name_list

    def get_goal_site_name(self):
        return self.goal_name


def horde_spawnable(level, turn):
    return turn.week >= HORDE_DELAY_BY_LEVEL[level - 1]

# certain site types have chance to throw off a horde   
class Horde(group.ActiveAIGroup):
    
    
    def __init__(self, site, game_map, actors):
        self.site = site
        owner = site.get_owner()
        level = site.get_level()
        super(Horde, self).__init__(owner, HORDE_RANGE, HORDE_AGGRESSION, owner.get_goal_funcs(),
                                    constraint_funcs = player_type.horde_constraints)
       
        self.type = random.choice([horde_type for horde_type in horde_types_by_name.values() if horde_type.level == level])
        self.update_goal(game_map, actors)
#        self.range = HORDE_RANGE
        self.leader = unit.Unit(unit.unit_types_by_name[self.type.leader_name])
        self.leader.set_trait(trait.MOUNTAINEER, True)
        
        self.add_unit(self.leader)
        self.add_unit_packet()
        self.reputation_value = self.get_level() * 2
#        self.set_hex(site.hex_loc)
#        site.hex_loc.add_group(self)
      
    def add_unit_packet(self):
        prev_leader_index = self.num_units() - 1
        for unit_type_name in self.type.unit_type_names:
            if not self.is_full():
                new_unit = unit.Unit(unit.unit_types_by_name[unit_type_name])
                new_unit.set_trait(trait.MOUNTAINEER, True)
                self.add_unit(new_unit)
            
        new_leader_index = self.num_units() - 1
        
        # keep leader at end of line
        self.move_unit(prev_leader_index, new_leader_index)
    
    def get_center_hex(self):
        return self.curr_hex   
    
    def has_goal(self):        
        return self.goal.is_active()
    
    def get_site(self):
        return self.site
    
    def get_goal(self):
        return self.goal.hex_loc
    
    def update_goal(self, game_map, actors):
        self.goal = random.choice(game_map.get_sites(filter_func = lambda curr_site : curr_site.get_owner() in actors))
        
    def get_target_player(self):
        return self.goal.get_owner()
    
    def get_level(self):
        return self.type.level
   
    def start_turn(self, turn_number, hex_map):
        super(Horde, self).start_turn(turn_number, hex_map)
        
        self.clear_dead_units()
        # as long as leader is alive, new units flock to the horde each turn
        if self.leader.is_alive():
            self.add_unit_packet()
   