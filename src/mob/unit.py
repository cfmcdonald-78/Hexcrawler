'''
Created on Jun 28, 2012

@author: Chris
'''
import move_mode
import trait
import core.event_manager as event_manager
from core.event_manager import Event
import file.name as name
import random

class UnitType(object):
    '''
    defines characteristics of types of mobs
    '''
    
    def __init__(self, name, descriptors, name_maker, is_army, is_combatant, level, strength, armor, speed, looting, health, traits):
        self.name = name
        self.descriptors = set(descriptors)
        self.name_maker = name_maker
        self.is_army = is_army
        self.is_combatant = is_combatant
        #self.is_monster = is_monster
        self.level = level
        self.strength = strength
        self.armor = armor
        self.speed = speed
        self.looting = looting
        self.traits = traits
        self.health = health
        self.used_names = {}
    
    def is_support(self):
        for support_trait in trait.support_traits:
            if support_trait in self.traits:
                return True
        return False
    
    def is_leader(self):
        for leader_trait in trait.leader_traits:
            if leader_trait in self.traits:
                return True
        return False 
    
    def gen_name(self, forced_pattern=None):
        return name.gen_name(self.name_maker, self.used_names, forced_pattern)

ROT_TIME = 3    # number of days until dead unit vanishes for good
DIPLOMAT_FRACTION = 0.33 # fraction of site income / day that diplomat can extract
BURN_WOUND_CHANCE = 0.5 # chance that unit that's burning at start of its turn will be wounded
MAX_ARMOR = 19  # ensures that armor can never reach 'auto succeed' level of 20


ARMY_TYPE = "Army"
UNIT_TYPE = "Unit"
HERO_TYPE = "Hero"

unit_types = []
unit_types_by_name = {}

def random_type_with_trait(desired_trait):
    return random.choice([curr_unit for curr_unit in unit_types if desired_trait in curr_unit.traits])

def random_hero_type():
    return random_type_with_trait(trait.HERO)
#def hero_types():
#    return unit_types_with_trait(trait.HERO)

#BASE_WOUNDS = 2

BASIC_MAINT_COST = -2

#
class Unit(object):
    '''
    party character
    '''

    def __init__(self, unit_type):
        '''
        Constructor
        '''
#        self.unit_type = unit_type
     
        #self.health = HEALTHY
        self.moves_left = unit_type.speed
#        self.naval_moves_left = 0
        self.traits = unit_type.traits.copy()
        self.strength = unit_type.strength
        self.armor = unit_type.armor
        self.armor_bonus = 0 
        self.type_name = unit_type.name
        self.name = unit_type.gen_name()
        self.level = unit_type.level
        self.looting = unit_type.looting
        self.speed = unit_type.speed
        self.army = unit_type.is_army
        self.combatant = unit_type.is_combatant
        self.support = unit_type.is_support()
   
        self.consumable_refresh_values = {}
        for consumable in trait.consumable_traits:
            if consumable in self.traits:
                self.consumable_refresh_values[consumable] = self.traits[consumable]
    
        self.wounds = 0
        self.health = unit_type.health
   
        self.group = None
        self.has_fought = False
    
    def has_fought_this_turn(self):
        return self.has_fought
    
    def get_type_text(self):
        return ARMY_TYPE if self.is_army() else UNIT_TYPE  
    
    def get_icon_name(self):
        return self.type_name
    
    def fought(self):
        self.has_fought = True
    
    def maintenance(self):
        if not self.is_army() or self.has_trait(trait.SUMMONED):
            return 0
        return self.level * BASIC_MAINT_COST
    
    def get_name(self):
        if len(self.name) > 0:
            return self.name
        else:
            return self.type_name

    def get_group(self):
        return self.group
    
    def set_group(self, new_group):
        self.group = new_group

    def get_ranged_strength(self, target):
        if (not target.is_army()) or self.is_army() or self.has_trait(trait.ARMY_ATTACK):
            strength = self.trait_value(trait.RANGED)
            strength += self.trait_value(trait.BLOOD_POWER)
            strength -= target.trait_value(trait.EVADE)  # EVADE makes it harder to hit with ranged attack
            return strength
        return 0
    
    def is_support(self):
        return self.support
    
    # base, unmodified strength
    def get_raw_strength(self):
        return self.strength
    
    # strength ignoring army vs. non-army combat
    def get_strength(self):
        strength = self.strength
            
        if self.is_wounded():
            strength += self.trait_value(trait.RAGE)

        strength -= self.trait_value(trait.RESTRAINED)
            
        strength += self.trait_value(trait.INSPIRED)
        assert (self.trait_value(trait.INSPIRED) == 0 or self.is_army())
        
        strength += self.trait_value(trait.BLOOD_POWER)
            
        strength -= self.trait_value(trait.EXHAUSTED) 
        assert (self.trait_value(trait.EXHAUSTED) <= self.get_raw_strength() / 2)
            
        return max (strength, 0)
    
    def get_combat_strength(self, target):
        if not target.is_army() or self.is_army() or self.has_trait(trait.ARMY_ATTACK):
            return self.get_strength()
        
        #if a non-army fights an army and doesnn't have "army attack", its strength is 0
        return 0
    
    def get_level(self):
        #TODO: hero level = level of highest level equipped item + 1
        return self.level
    
    def get_looting(self):
        return self.looting
    
    def has_trait(self, check_trait):
        if check_trait in trait.negating_traits:
            if trait.negating_traits[check_trait] in self.traits:
                return False
        return check_trait in self.traits
    
    def consume_trait(self, trait):
        if self.traits.get(trait, 0) > 0:
            self.set_trait(trait, self.trait_value(trait) - 1, take_highest=False)
            return True
        return False
    
    def refresh_trait(self, refreshed):
        if refreshed in self.traits and refreshed in self.consumable_refresh_values:
            self.set_trait(refreshed, self.consumable_refresh_values[refreshed])
    
    def use_trait(self, use_trait):
        assert(use_trait in trait.useable_traits)
        if self.consume_trait(use_trait):
            self.group.trait_used(self, use_trait)
            #event_manager.queue_event(Event(event_manager.TRAIT_USED, [self, use_trait]))
            # call trait func? trigger trait event?
            return
    
    def set_trait(self, mod_trait, value, take_highest=True):
        if mod_trait == trait.RESTRAINED and self.has_trait(trait.UNCHAINABLE):
            return
        if mod_trait == trait.BURNING and self.has_trait(trait.FLAMEPROOF):
            return
        
        old_value = self.trait_value(mod_trait)
        new_value =  max(value, old_value) if take_highest else value
        self.traits[mod_trait] = new_value
        
#        if trait == SLOWED:
        # TODO: this doesn't work - how do you notify group of change in move capability?
#            # immediately impose move penalty
#            self.moves_left = max(0, self.moves_left - (new_value - old_value))
#    
    def remove_trait(self, trait):
        if trait in self.traits:
            del self.traits[trait]
    
    def get_traits(self):
        return self.traits
    
    def trait_value(self, trait):
        if trait in self.traits:
            return self.traits[trait]
        return 0
    
    def set_armor_bonus(self, new_bonus):
        self.armor_bonus = new_bonus
    
    def get_health(self):
        return self.health
    
    def get_armor(self):
        armor = self.armor
        if self.is_wounded():
            armor -= self.trait_value(trait.RAGE)
        return min(armor + self.armor_bonus, MAX_ARMOR)
    
    def is_army(self):
        return self.army
    
    def is_combatant(self):
        return self.combatant
    
    def curr_wounds(self):
        return self.wounds
    
    def max_wounds(self):
        return self.health + self.trait_value(trait.EXTRA_WOUND)
    
    def is_alive(self):
        return self.wounds < self.max_wounds()
        #return self.health != DEAD
    
    def is_healthy(self):
        return self.wounds == 0
    
    def is_wounded(self):
        return self.is_alive() and self.wounds > 0
        #return self.health == WOUNDED
    
    def wound(self, number=1):
        if not self.is_alive():
            raise ValueError("Wounded an already dead character.")
        self.wounds = min(self.wounds + number, self.max_wounds())
        #self.health -= 1
#        if self.health < DEAD:
#            
        
        if not self.is_alive(): #self.health == DEAD:
            self.set_trait(trait.ROTTING, ROT_TIME)
    
    def disband(self):
        pass
    
    def get_owner(self):
        return self.group.get_owner()
    
    def heal(self):
        assert(self.is_wounded())
        self.wounds -= 1

    def revive(self):
        assert(not self.is_alive())
        self.wounds -= 1
        del self.traits[trait.ROTTING]

    def move(self, move_cost):
        self.moves_left -= move_cost
#        self.naval_moves_left = max(0, self.naval_moves_left - move_cost)
    
    def get_max_moves(self):
#        if self.get_group()!= None and self.get_group().get_move_mode() == move_mode.NAVAL:
#            return self.get_group().get_highest_trait(NAVAL)
#        else:
        return self.speed
    
    def get_moves_left(self):
#        if self.get_group()!= None and self.get_group().get_move_mode() == move_mode.NAVAL:
#            return self.group.moves_left
#        else:
        return self.moves_left
    
    
    def get_move_mode(self):
        if self.get_group() != None:
            return self.get_group().get_move_mode()
        else:
            return move_mode.FOOT
    
#    def get_naval_moves_left(self):
#        return self.naval_moves_left
#    
#    def get_naval_moves(self):
#        return self.naval_moves_left
#    
    def can_use_items(self):
        return False
    
    def hire_cost(self, hiring_group):
        discount = (0 if hiring_group == None else hiring_group.get_highest_trait(trait.HAGGLER) * 0.05)
        return int(20 * self.get_level() * (1 - discount))
    
    def will_join(self, acquiring_player):
        if self.has_trait(trait.HONOR) and self.trait_value(trait.HONOR) > acquiring_player.get_reputation():
            return False, "reputation too poor" 
        if self.has_trait(trait.WILD) and self.trait_value(trait.WILD) > acquiring_player.num_sites():
            return False, "too many sites"
        if self.has_trait(trait.AVARICE) and self.trait_value(trait.AVARICE) > acquiring_player.get_gold():
            return False, "not enough gold"
        return True, None
        
    def start_turn(self, curr_hex, turn_number):
        self.moves_left = self.speed
#        self.naval_moves_left = self.trait_value(NAVAL)
        self.has_fought = False
        
        if self.is_wounded():
            if curr_hex.heals_unit():
                self.heal()
        if not self.is_alive() and self.has_trait(trait.REGENERATE):
            self.revive()
        
        # all units become unrestrained at start of turn
        if self.has_trait(trait.RESTRAINED):
            self.remove_trait(trait.RESTRAINED)
        
        # summon countdown: at 0 will be disbanded
        if self.has_trait(trait.SUMMONED):
            self.traits[trait.SUMMONED] -= 1
            
        if self.has_trait(trait.ROTTING):
            self.traits[trait.ROTTING] -= 1
        