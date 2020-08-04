'''
Created on Jul 20, 2012

@author: Chris
'''
STARTING_GOLD = 100
import reputation, gamemap.hexgrid as hexgrid
import random, collections
import gamemap.mask as mask
import mob.trait as trait
  
def get_closest(curr_hex, hex_list, test):
    valid_hexes = [hex_loc for hex_loc in hex_list if test(hex_loc)]
    if len(valid_hexes) > 0:
        valid_hexes.sort(key = lambda hex_loc : hexgrid.get_distance(hex_loc, curr_hex))
        return valid_hexes[0]
    return None

def retake_site(active_group, hexes_in_range, player_mask):
    curr_hex = active_group.get_hex()
    retake_hex = get_closest(curr_hex, hexes_in_range, lambda hex_loc : player_mask.get_visibility(hex_loc.x, hex_loc.y) != mask.NEVER_VISIBLE
                            and hex_loc.has_site() and hex_loc.site.is_active() and active_group.is_hostile(hex_loc.site.get_owner()) 
                            and hex_loc.site.default_owner == active_group.get_owner())
 
    return retake_hex

def take_site(active_group, hexes_in_range, player_mask):
    curr_hex = active_group.get_hex()
    take_hex = get_closest(curr_hex, hexes_in_range, lambda hex_loc : player_mask.get_visibility(hex_loc.x, hex_loc.y) != mask.NEVER_VISIBLE
                            and hex_loc.has_site() and hex_loc.site.is_active() and active_group.is_hostile(hex_loc.site.get_owner()))
 
    return take_hex

def assassin_target(active_group, hexes_in_range, player_mask):
    curr_hex = active_group.get_hex()
    target_hex = get_closest(curr_hex, hexes_in_range, lambda hex_loc : hex_loc.get_defenders() != None and
                        hex_loc.get_defenders().get_owner().is_actor() and hex_loc.get_defenders().has_trait(trait.HERO))
    
    return target_hex
    
def attack_active_enemy(active_group, hexes_in_range, player_mask):
    curr_hex = active_group.get_hex()
    active_enemy_hex = get_closest(curr_hex, hexes_in_range, lambda hex_loc : (hex_loc.active_group != None and hex_loc.active_group != None 
                                                                               and hexgrid.get_distance(hex_loc, curr_hex) <= active_group.aggression_range
                                                                               and active_group.is_hostile(hex_loc.active_group.get_owner())
                                                                               and player_mask.get_visibility(hex_loc.x, hex_loc.y) == mask.VISIBLE))
    return active_enemy_hex

def move_to_settled(active_group, hexes_in_range, player_mask):
    curr_hex = active_group.get_hex()
    settled_hex = get_closest(curr_hex, hexes_in_range, lambda hex_loc : hex_loc.is_settled() and not hex_loc.has_occupants()
                              and player_mask.get_visibility(hex_loc.x, hex_loc.y) != mask.NEVER_VISIBLE)    
    return settled_hex

def stay_in_zone(active_group, hexes_in_range, player_mask):
    group_center = active_group.get_center_hex()
    return [hex_loc for hex_loc in hexes_in_range if hex_loc.get_zone() == group_center.get_zone()]
    

def avoid_friendly_sites(active_group, hexes_in_range, player_mask):
     return [hex_loc for hex_loc in hexes_in_range if not hex_loc.has_site() or active_group.is_hostile(hex_loc.site.get_owner())]

zone_patrol_constraints = [stay_in_zone, avoid_friendly_sites]
neutral_constraints = []
chaos_constraints = []
assassin_goals = [assassin_target]
neutral_goals = [retake_site, attack_active_enemy, move_to_settled]
chaos_goals = [attack_active_enemy, take_site, move_to_settled]

def move_active_group(active_group, dest_groups, hexes_in_range, player_mask):
    
    hexes_in_range = [hex_loc for hex_loc in hexes_in_range if hex_loc not in dest_groups
                            and not hex_loc.has_friendlies(active_group) and hex_loc.legal_move(active_group)]
    
    # limit available hexes based on group's constraints
    for constraint_func in active_group.get_constraint_funcs():
        hexes_in_range = constraint_func(active_group, hexes_in_range, player_mask)
        
    
    # try to pick a hex based on group's goal funcs
    target = None
    for goal_func in active_group.get_goal_funcs():
        target = goal_func(active_group, hexes_in_range, player_mask)
        if target != None:
            return target
    
    # if group has specific goal, head towards it
    if active_group.has_goal():
        # move towards goal
        return active_group.get_goal()
        
    # Otherwise, move to random empty hex 
    empty_hexes = [hex_loc for hex_loc in hexes_in_range if not hex_loc.has_occupants()
                   and player_mask.get_visibility(hex_loc.x, hex_loc.y) == mask.VISIBLE]
    if len(empty_hexes) > 0:
        chosen_hex =  random.choice(empty_hexes)
        return chosen_hex
    else:
        return active_group.get_hex()


MONSTER = "Monster"
HUMAN = "Human"
NEUTRAL = "Neutral"

active_group_goal_funcs = {"monster_patrol": chaos_goals, "neutral_patrol": neutral_goals, "assassin_patrol": assassin_goals}

class NPCPlayerType(object):
    
    def __init__(self, name, base_type,  color,patrol_reputation, patrol_func_name, 
                 hostile_to, hostility_func_name, hostility_table):
        self.name = name
        self.base_type = base_type
        self.patrol_func_name = patrol_func_name
        self.patrol_reputation = patrol_reputation
        self.color = color
        self.hostile_to = hostile_to
        self.hostility_func_name = hostility_func_name
        self.hostility_table = hostility_table
        
npc_player_types = []
