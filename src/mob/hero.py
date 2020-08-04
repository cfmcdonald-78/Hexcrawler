'''
Created on Aug 11, 2012

@author: Chris
'''
import mob.unit as unit, mob.trait as trait
import hexcrawl.reputation as reputation, hexcrawl.income as income
import mob.item as item
from util.tools import max_in_list
import core.event_manager as event_manager
from core.event_manager import Event

NUM_EQUIP_SLOTS = {item.ARMOR: 1, item.WEAPON: 1, item.MISC_ITEM: 2}
EQUIP_SLOTS = [item.ARMOR, item.WEAPON, item.MISC_ITEM, item.MISC_ITEM]

BACKPACK_SIZE = 3

HERO_COST_MULTIPLIER = 5

class Hero(unit.Unit):
    
    def __init__(self, hero_type):
        assert(trait.HERO in hero_type.traits)
        super(Hero, self).__init__(hero_type)
        self.equipped_items = []
        self.owner = None
        self.curr_traits = self.traits.copy()
    
        self.num_equipped_items = {}
        for item_type in EQUIP_SLOTS:
            self.equipped_items.append(None)
            self.num_equipped_items[item_type] = 0
        self.num_backpack_items = 0
        self.backpack_items = []
        for i in range(BACKPACK_SIZE):
            self.backpack_items.append(None)
      
    def get_type_text(self):  
        return unit.HERO_TYPE
    
    def get_owner(self):
        return self.owner
    
    def hire_cost(self, hiring_group):
        base_cost = super(Hero, self).hire_cost(hiring_group)
        return base_cost * HERO_COST_MULTIPLIER
    
    def set_group(self, new_group):
        super(Hero, self).set_group(new_group)
        
        # update ownership status
        if self.owner == None and new_group.get_owner() != None:
            self.owner = new_group.get_owner()
            self.owner.add_hero(self)
      
    def wound(self):
        super(Hero, self).wound()
        if not self.is_alive():
            self.owner.remove_hero(self)
    
    def disband(self):
        super(Hero, self).disband()
        self.owner.remove_hero(self)
    
    def revive(self):
        super(Hero, self).revive()
        self.owner.add_hero(self)
    
    def can_use_items(self):
        return True
    
    def get_equipped_item(self, index):
        return self.equipped_items[index]
    
    def get_backpack_item(self, index):
        return self.backpack_items[index]
    
    def discard_item(self, old_item):
      
        was_equipped = False
        if old_item in self.equipped_items:
            was_equipped = True
            index = self.equipped_items.index(old_item)
            self.equipped_items[index] = None
            self.num_equipped_items[old_item.get_type()] -= 1
        else:
            self.remove_from_backpack(old_item)
        
        # negative traits are adjusted when an item is acquired/discarded,
        # if item was equipped, also need to adjust positive traits
        self.update_stats(old_item, False, False)
        if was_equipped:
            self.update_stats(old_item, True, False)
        
        # adjust level to match that of highest level item, to min. of 1
        self.level = 1
        for curr_item in (self.equipped_items + self.backpack_items):
            self.level = max(self.level, 0 if curr_item == None else curr_item.get_level())     
        return True
    
    def equip_slots_full(self, item_type):
        return self.num_equipped_items[item_type] >= NUM_EQUIP_SLOTS[item_type]   
    
    def backpack_full(self):
        return self.num_backpack_items == BACKPACK_SIZE
    
    def put_in_backpack(self, new_item):
        if self.backpack_full():
            return False
    
        for i in range(BACKPACK_SIZE):
            if self.backpack_items[i] == None:
                self.backpack_items[i] = new_item
                self.num_backpack_items += 1
                return True
                
        assert(False)
    
    def remove_from_backpack(self, old_item):
        index = self.backpack_items.index(old_item)
        self.backpack_items[index] = None
        self.num_backpack_items -= 1
        
    def add_item(self, new_item):
        if not self.put_in_backpack(new_item):
            if not self.can_equip_item(new_item):
                # no room!
                return False
            else:
                self.equip_item(new_item)
        
        self.update_stats(new_item, False, True)
        
        # adjust level to match that of highest level item
        self.level = max(self.level, new_item.get_level())
        return True
    
    def can_equip_item(self, new_item):
        if not self.equip_slots_full(new_item.get_type()):
            return True
        
        if not self.backpack_full():
            return True # can equip by dumping a currently equipped item to backpack
        
        if new_item in self.backpack_items:
            return True  # can equip by swapping with item being equipped
         
        return False
    
    def get_traits(self):
        return self.curr_traits
       
    def update_traits(self):
        traits = self.traits.copy()
        for curr_item in self.equipped_items:
            if curr_item == None:
                continue
            
            item_traits = curr_item.get_traits()
            for curr_trait in item_traits:   
                if curr_trait in trait.consumable_traits:
                    traits[curr_trait] = traits.get(curr_trait, 0) + item_traits[curr_trait]
                elif curr_trait not in trait.stat_mods:
                    traits[curr_trait] = max(traits.get(curr_trait, 0), item_traits[curr_trait])
        self.curr_traits = traits
        
    def trait_value(self, trait):
        return self.curr_traits.get(trait, 0)
    
    def has_trait(self, trait):
        return trait in self.curr_traits
    
    def set_trait(self, mod_trait, value, take_highest=True):
        super(Hero, self).set_trait(mod_trait, value, take_highest)
        self.update_traits()
    
    def remove_trait(self, trait):
        super(Hero, self).remove_trait(trait)
        self.update_traits()
    
    def consume_trait(self, trait):
        ret_val = False
        
        if super(Hero, self).consume_trait(trait):
            ret_val = True
        else:
            for curr_item in self.equipped_items:
                if curr_item != None and curr_item.consume_trait(trait):
                    ret_val = True
                    break
        
        if ret_val == True:
            self.curr_traits[trait] = self.curr_traits[trait] - 1
            event_manager.queue_event(Event(event_manager.UNIT_STATS_CHANGED, [self]))
        return ret_val
   
    def refresh_trait(self, refreshed_trait):
        super(Hero, self).refresh_trait(refreshed_trait)
        
        for curr_item in self.equipped_items:
            if curr_item != None:
                curr_item.refresh_trait(refreshed_trait)
        for curr_item in self.backpack_items:
            if curr_item != None:
                curr_item.refresh_trait(refreshed_trait)
                
        refreshed_value = self.traits.get(refreshed_trait, 0)
        for curr_item in self.equipped_items:
            if curr_item != None:
                refreshed_value += curr_item.trait_value(refreshed_trait)
        if refreshed_value != 0:
            self.curr_traits[refreshed_trait] = refreshed_value
            
    def update_stats(self, stat_item, equipping, adding):
        
        for mod_stat in [curr_trait for curr_trait in stat_item.get_traits() if curr_trait in trait.stat_mods]:
            stat_mod_value = stat_item.get_traits()[mod_stat]
            # negative stat adjustments are adjusted on add/remove from inventory, positive 
            # adjustments on add/remove from equipment
            if (stat_mod_value < 0) == equipping:
                continue
            
            # if item coming off, reverse mod
            if not adding:
                stat_mod_value = -stat_mod_value
        
            if mod_stat == trait.STRENGTH_MOD:
                self.strength += stat_mod_value
            elif mod_stat == trait.ARMOR_MOD:
                self.armor += stat_mod_value
            elif mod_stat == trait.SPEED_MOD:
                self.speed += stat_mod_value
            elif mod_stat == trait.LOOT_MOD:
                self.looting += stat_mod_value
            elif mod_stat == trait.REPUTATION_MOD:
                rep_adj_type = reputation.ITEM_EQUIP if adding else reputation.ITEM_UNEQUIP
                reputation.adjust_reputation(rep_adj_type, stat_item, self.owner, delta=stat_mod_value)
            elif mod_stat == trait.INCOME_MOD:
                self.owner.adjust_income(stat_mod_value, income.ITEM_INCOME)
                
        event_manager.queue_event(Event(event_manager.UNIT_STATS_CHANGED, [self]))
        
    def equip_item(self, new_item):
        assert(self.can_equip_item(new_item))
        
        # if added item in backpack, move it out
        if new_item in self.backpack_items:
            self.remove_from_backpack(new_item)
        
        # if there's an empty equip slot, put item there
        if not self.equip_slots_full(new_item.get_type()):
            for i in range(len(EQUIP_SLOTS)):
                if new_item.get_type() == EQUIP_SLOTS[i] and self.equipped_items[i] == None:
                    self.equipped_items[i] = new_item
                    break
        else:
            # otherwise unequip a currently equipped item
            for i in range(len(EQUIP_SLOTS)):
                if new_item.get_type() == EQUIP_SLOTS[i]:
                    self.unequip_item(self.equipped_items[i])
                    self.equipped_items[i] = new_item
                    break
        
        self.num_equipped_items[new_item.get_type()] += 1
        
        self.update_stats(new_item, True, True)
        self.update_traits()
    
    def can_unequip_item(self):
        return not self.backpack_full()
    
    
    def unequip_item(self, old_item):
        assert(self.can_unequip_item())
        index = self.equipped_items.index(old_item)

        self.equipped_items[index] = None
        self.num_equipped_items[old_item.get_type()] -= 1
        self.put_in_backpack(old_item)
    
       # old_traits = old_item.get_traits()
        self.update_stats(old_item, True, False)
        self.update_traits()
    
    def get_level(self):
        #TODO: hero level = level of highest level equipped item + 1
        return self.level