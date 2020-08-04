'''
Created on Jul 20, 2012

@author: Chris
'''
from collections import namedtuple
import random
import mob.trait as trait

ItemModifier = namedtuple("ItemModifier", ['adjective', 'types', 'level', 'traits'])
BaseItem = namedtuple("BaseItem", ['name', 'type', 'subtype', 'quality', 'level', 'traits'])

item_modifiers = []
base_items = []

ARTIFACT_QUALITY = "artifact"
NORMAL_QUALITY = "normal"

MISC_ITEM = "Misc"
WEAPON = "Weapon"
ARMOR = "Armor"
MAIL = "Mail"
SHIELD = "Shield"
MELEE = "Melee"
RANGED = "Ranged"
HELD = "Held"
POTION = "Potion"
JEWELRY = "Jewelry"
CLOTHING = "Clothing"
TRANSPORT = "Transport"

item_types = [ARMOR, WEAPON, MISC_ITEM]
item_subtypes = [MAIL, SHIELD, MELEE, RANGED, HELD, POTION, JEWELRY, CLOTHING, TRANSPORT]

GOLD_VALUE_PER_LEVEL = {NORMAL_QUALITY: 25, ARTIFACT_QUALITY: 40}

OTHER_MODIFIER_CHANCE = 0.5
MISC_MODIFIER_CHANCE = 0.8

#class ItemType(object):
#    '''
#    classdocs
#    '''
#
#    def __init__(self, name, traits):
#        pass

# combine traits of base item with traits of modifier. If both have same trait they better be
# boolean (in which case merge is just True, since boolean traits are always true), or integers (in which case merge is sum)
def merge_traits(base_traits, mod_traits):
    merged_traits = base_traits.copy()
    for trait in mod_traits:
        if trait in merged_traits:
            if isinstance(merged_traits[trait], int):
                assert(isinstance(mod_traits[trait], int))
                merged_traits[trait] += mod_traits[trait]
            else:
                assert(isinstance(mod_traits[trait], bool))
        else:
            merged_traits[trait] = mod_traits[trait]
        # no point in having traits that do nothing hanging around
        if merged_traits[trait] == 0:
            del merged_traits[trait]
            
    return merged_traits

def type_by_name(base_item_name):
    result = [base_item for base_item in base_items if base_item.name == base_item_name]
    if len(result) == 1:
        return result[0]

def random_item(item_level, item_quality):
    candidates = [base_item for base_item in base_items if base_item.level == item_level and base_item.quality == item_quality]
        
    if len(base_items) == 0:
        return None
        
    return Item(random.choice(candidates))
        
class Item(object):
    '''
    classdocs
    '''
    
    def __init__(self, base, base_only=False):
        self.base = base
#        self.level = base.level
#        self.type = base.type
#        self.subtype = base.subtype
#        self.quality = base.quality
        # if weapon/armor, chance of additional modifying trait. if misc. item, higher chance 
        modifier = None
        modifier_chance = MISC_MODIFIER_CHANCE if base.type == MISC_ITEM else OTHER_MODIFIER_CHANCE
        if not base_only and random.random() <= modifier_chance:
            modifier = random.choice([mod for mod in item_modifiers if mod.level <= base.level and (base.type in mod.types or
                                                                                                    base.subtype in mod.types)])
    
       # self.name = base.name
        if modifier != None:
            self.name = modifier.adjective + " " + base.name  
            self.traits = merge_traits(base.traits, modifier.traits)  
        else:
            self.name = base.name
            self.traits = base.traits
        
        self.consumable_refresh_values = {}
        for consumable in trait.consumable_traits:
            if self.has_trait(consumable):
                self.consumable_refresh_values[consumable] = self.trait_value(consumable)
        # merge traits
    
    def trait_value(self, trait):
        return self.traits.get(trait, 0)
    
    def set_trait(self, trait, value):
        self.traits[trait] = value
    
    def has_trait(self, trait):
        return trait in self.traits

    def consume_trait(self, trait):
        if self.trait_value(trait) > 0:
            self.set_trait(trait, self.trait_value(trait) - 1)
            return True
        return False
    
    def refresh_trait(self, trait):
        if self.has_trait(trait):
            self.set_trait(trait, self.consumable_refresh_values[trait])
    
    def get_traits(self):
        return self.traits
    
    def get_name(self):
        return self.name
    
    def get_level(self):
        return self.base.level
    
    def get_gold_value(self):
        return self.get_level() * GOLD_VALUE_PER_LEVEL[self.base.quality]
    
    def get_type(self):
        return self.base.type
    
    def get_icon(self):
         # TODO: diff icons for diff. subtypes
        return self.base.subtype