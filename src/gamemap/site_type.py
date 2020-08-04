'''
Created on Jul 9, 2012

@author: Chris
'''
from collections import namedtuple
import mob.unit as unit
import file.name as name
import math

Garrison = namedtuple('Garrison', ['is_army', 'min', 'max', 'leader_chance', 'depth'])
Spawn = namedtuple('Spawn', ['type', 'chance_per_day', 'range', 'aggression', 'units'])
LootEffects = namedtuple('LootEffects', ['new_status', 'gold', 'reputation', 'item', 'prisoner'])
Misc = namedtuple('Misc', ['haven', 'zone_center', 'settlement', 'income', 'reactivate_chance'])

ZONE_PATROL = "zone_patrol"
WANDERER = "wanderer"

VILLAIN_PRISONER = "villain"
NORMAL_PRISONER = "normal"
NO_PRISONER = "none"

NO_ITEM = "none"

def compute_flat_aggression(site):
    return site.site_type.aggression_amount

def compute_per_level_aggression(site):
    return int(math.ceil(site.get_level() * site.site_type.aggression_amount))

def compute_flat_income(game_map, site):
    return site.site_type.income_amount * site.get_level()

def compute_settled_hex_income(hex_map, site):
    return int(site.get_level() * site.site_type.income_amount * hex_map.count_settled_hexes(site.hex_loc, site.get_settle_range()) )

def compute_forest_hex_income(hex_map, site):
    return int(site.get_level() * site.site_type.income_amount * hex_map.count_settled_hexes(site.hex_loc, site.get_settle_range()) )

income_func_table =  {"flat": compute_flat_income, "per_settled_hex": compute_settled_hex_income, 
                      "per_forest_hex": compute_forest_hex_income}


aggression_range_table = {"flat": compute_flat_aggression, "per_level": compute_per_level_aggression}

# site statuses
ACTIVE = "Active"
SACKED = "Sacked"
DESTROYED = "Destroyed"

# patrol types
#ARMY_PATROL = "army"  

def dict_update(update_dict, unit_type):
    if unit_type.level in update_dict:
        update_dict[unit_type.level].append(unit_type)
    else:
        update_dict[unit_type.level] = [unit_type]  


class SiteType(object):
    def __init__(self, name, name_maker, owner_name, legal_terrain, garrison_info,  spawn_info, loot_effects, misc_info):
        self.name = name
        self.owner_name = owner_name
        
        self.name_maker = name_maker
        self.used_names = {}
        
        self.haven = misc_info.haven    # havens are protected from attack 
        self.zone_centered = misc_info.zone_center
        self.settle_effect = misc_info.settlement
        self.income_func = income_func_table[misc_info.income['type']]
        self.income_amount = misc_info.income['amount'] 
        self.aggression_range_func = None if spawn_info == None else aggression_range_table[spawn_info.aggression['type']]
        self.aggression_amount = None if spawn_info == None else spawn_info.aggression['amount']
        self.reactivate_chance = misc_info.reactivate_chance
        
        self.spawn_info = spawn_info
        
        self.legal_terrain = legal_terrain
        self.garrison_info = garrison_info
        self.unit_types = [candidate for candidate in unit.unit_types if self.name in candidate.sites]
        self.army_units = {}
        self.character_units = {}
        self.leader_units = {}
        self.non_combatants = {}
        for candidate in self.unit_types:
            if candidate.is_combatant:
                if candidate.is_army:
                    dict_update(self.army_units, candidate)
                else:
                    dict_update(self.character_units, candidate)
                if candidate.is_support():
                    dict_update(self.leader_units, candidate)
            else:
                dict_update(self.non_combatants, candidate)
        
        self.tight_quarters = garrison_info != None and not garrison_info.is_army 
        self.loot_effects = loot_effects
    
    #  Possibility: alternative name generator based on statistical analysis: randomly pick bigram of starting letters, then pick each subsequent letter
    #    based on frequency count.  Data set town names in britain and germany
    
    def get_non_combatants(self, level):
        return self.non_combatants.get(level, [])
    
    def get_units(self, level, is_army):
        candidates_dict = self.army_units if is_army else self.character_units
        return candidates_dict.get(level, [])
        
    def garrison_candidates(self, level):
        return self.get_units(level, self.garrison_info.is_army)
        
    def gen_name(self):
        return name.gen_name(self.name_maker, self.used_names)
    
    def get_name(self):
        return self.name
    
site_types = {}