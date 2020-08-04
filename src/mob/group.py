'''
Created on Jun 28, 2012

@author: Chris
'''
import mob.unit as unit, mob.trait as trait
from core.event_manager import Event
from util.tools import DoublyLinkedObject
import core.event_manager as event_manager
import hexcrawl.player_type as player_type
import gamemap.site_upgrade as site_upgrade
import move_mode
import random

MAX_UNITS = 8
GROUP_BASE_SIGHT = 2

class Group(DoublyLinkedObject):
    '''
    represents the party (1+ characters) and/or army (1+ units) residing in a given hex.
    '''
    
    def __init__(self, owner):
        '''
        Constructor
        '''
        super(Group, self).__init__()
        self.units = []
        self.curr_hex = None
        self.owner = owner
#        self.next = self.previous = None  # groups are on doubly-linked circular list, pointers set in player.add_group()
        if owner != None:
            owner.add_group(self)
        else: 
            assert(isinstance(self, HireGroup))
        self.moves_left = 0
        self.move_mode = move_mode.FOOT
        self.scout_bonus = 0
        self.avg_level = 0
        self.reputation_value = 0
        self.live_unit_count = 0
        self.last_diplo_income = 0
#        self.fought_this_turn = False
#        self.dead_unit_index = 0
    
    def __str__(self):
        result = "owner: " + ("" if self.owner == None else self.owner.name)
        result += " type: " + self.__class__.__name__ 
        for curr_unit in self.units:
            result += " unit " + curr_unit.get_name() + " alive: " + str(curr_unit.is_alive())
        return result
    
    def is_full(self):
        return len(self.units) == MAX_UNITS
    
    def is_active(self):
        return self.owner != None
    
    # return true if this group is hostile to a given player
    def is_hostile(self, other_player):
        return self.owner.is_hostile(self, other_player)
    
    def can_merge(self, new_group):
        if new_group.owner != self.owner:
            return False
        if len(self.units) + len(new_group.units) > MAX_UNITS:
            return False
        return True
    
    def get_level(self):
        return self.avg_level
    
    def compute_level(self):
        num_units = 0
        total_level = 0
        for curr_unit in self.units:
            num_units += 1
            total_level += curr_unit.get_level()
        
        self.avg_level = 0 if num_units == 0 else int(round(total_level / float(num_units)))
            
    def merge(self, new_group):
        if not self.can_merge(new_group):
            raise ValueError("attempted illegal merge of " + str(new_group) + " into " + str(self))
        
        for new_unit in new_group.units:
            self.add_unit(new_unit, transfer=True)
        new_group.owner.remove_group(new_group)
        self.update_trait_effects()
        self.compute_level()
    
    # consume movement points, used internally, and by combat module 
    # to reduce move after attack that didn't oust enemy
    def consume_movement(self, amount):
        for unit in self.units:
            unit.move(amount)
        self.moves_left -= amount
    
    def get_move_mode(self):
        return self.move_mode
    
    #def is_flying(self):
        # ARMY_FLIGHT unit can carry rest of group, otherwise every unit in group must have flying 
        
    def is_aquatic(self):
        return all([curr_unit.has_trait(trait.AQUATIC) for curr_unit in self.units])
    
    # return True if indices 1 and 2 straddle the dead unit boundary.
    # in that case, a user-initiate swap of those units is illegal
    def dead_unit_crossing(self, index1, index2):
        return self.units[index1].is_alive() != self.units[index2].is_alive()

    def clear_dead_units(self):
        # clean out dead units
        i = 0
        while i < len(self.units):
            curr_unit = self.units[i]
            if not curr_unit.is_alive():
                self.remove_unit(curr_unit)
            else:
                i += 1
    
    def move(self, new_hex, move_cost):
        self.consume_movement(move_cost)
        self.curr_hex.remove_group(self)
        self.owner.get_mask().seer_removed(self.get_hex(), self.get_sight_range())
        new_hex.add_group(self)
        self.update_burn_state()
    
    def move_unit(self, curr_index, new_index):
        self.units.insert(new_index, self.units.pop(curr_index))
    
    # set transfer to true if unit is just moving btw. groups, true if it's actually being disbanded/destroyed
    def remove_unit_at_index(self, index_to_remove, transfer=False):
        unit_to_remove = self.units[index_to_remove]
        return self.remove_unit(unit_to_remove, transfer=transfer)
    
     # set transfer to true if unit is just moving btw. groups, true if it's actually being disbanded/destroyed
    def remove_unit(self, unit_to_remove, transfer=False):
        if unit_to_remove.is_alive():
            self.live_unit_count -= 1
            
        self.units.remove(unit_to_remove)
        event_manager.queue_event(Event(event_manager.UNIT_REMOVED, [self]))

        if not transfer:
            self.owner.lose_unit(unit_to_remove)

        self.compute_level()
        self.update_trait_effects()
        unit_to_remove.set_group(None)
       
        return unit_to_remove
    
    def get_hex(self):
        return self.curr_hex
    
    def set_hex(self, curr_hex):
        self.curr_hex = curr_hex
        self.owner.get_mask().seer_added(self.get_hex(), self.get_sight_range())
        self.update_trait_effects()
    
    def add_item(self, new_item):
        for curr_unit in self.units:
            if curr_unit.can_use_items():
                if curr_unit.add_item(new_item):
                    return True
        return False # Either no unit who can use items, or everyone who can has no room for this item
    
    # bypasses all checks, used by ownerless HireGroup
    def do_add(self, new_unit, index=None):
        if self.num_units() == MAX_UNITS:
            return False
        
        if index == None:
            if new_unit.is_alive():
                # insert new unit after last alive unit
                try:
                    index = [curr_unit.is_alive() for curr_unit in self.units].index(False) 
                except ValueError:
                    index = self.num_units()
            else:
                index = self.num_units()
        
        self.units.insert(index, new_unit)
        new_unit.set_group(self)
        return True
    
    def add_unit(self, new_unit, index=None, transfer=False):
        if not self.do_add(new_unit, index):
            return
        
        event_manager.queue_event(Event(event_manager.UNIT_ADDED, [self]))
        
        if new_unit.is_alive():
            self.live_unit_count += 1
        
        if not transfer:
            self.owner.gain_unit(new_unit)
        
        self.compute_level()
        if self.curr_hex != None:
            self.update_trait_effects()
        
        return True
        
    def get_moves_left(self):
        return self.moves_left

    def get_max_moves(self):
        return min([curr_unit.get_max_moves() for curr_unit in self.units])
    
    def get_owner(self):
        return self.owner
        
    def get_site(self):
        return None
    
    def has_unit(self, check_unit):
        return check_unit in self.units
        
    def get_unit(self, index):
        if index < 0 or index >= len(self.units):
            return None
        return self.units[index]
    
    def num_units(self):
        return len(self.units)

    def num_live_units(self):
        return self.live_unit_count

    def wounded(self):
        healthy_count = 0
        # need exception code to handle possible race condition with live_unit_count when unit is removed by another thread
        try:
            for i in range(self.live_unit_count):
                if self.units[i].is_healthy():
                    healthy_count += 1
                if healthy_count > self.live_unit_count / 2:
                    return False
            return True
        except IndexError:
            print "index out of bounds in group.wounded(), retrying"
            return self.wounded()
        
    def healthy(self):
        # need exception code to handle possible race condition with live_unit_count when unit is removed by another thread
        try:
            for i in range(self.live_unit_count):
                if not self.units[i].is_healthy():
                    return False
            return True
        except IndexError:
            print "index out of bounds in group.healthy(), retrying"
            return self.healthy()

    def has_trait(self, trait):
        for curr_unit in self.units:
            if curr_unit.is_alive() and curr_unit.has_trait(trait):
                return True
        return False
    
    def all_has_trait(self, trait):
        for curr_unit in self.units:
            if curr_unit.is_alive() and not curr_unit.has_trait(trait):
                return False
        return True
    
#    # set trait on all units in group
    def set_trait(self, trait, value):
        for curr_unit in self.units:
            curr_unit.set_trait(trait, value)
    
    # returns the highest value of the given trait in this group, or 0, if it isn't present
    def get_highest_trait(self, trait):
        highest_value = 0
        
        for curr_unit in self.units:
            if curr_unit.is_alive() and curr_unit.has_trait(trait):
                trait_value = curr_unit.trait_value(trait)
                highest_value = max(highest_value, trait_value)
        
        return highest_value

    def army_fraction(self):
        army_fraction = 0.0
        num_units = self.num_units()
        
        for curr_unit in self.units:
            if curr_unit.is_army():
                army_fraction += 1.0 / num_units
        return army_fraction
    
    # reputation adjustment caused by destroying this group
    def set_reputation_value(self, reputation_value):
        self.reputation_value = reputation_value
        
    def get_reputation_value(self):
        return self.reputation_value

    def has_live_units(self):
        return self.live_unit_count > 0
#        return any([curr_unit.is_alive() for curr_unit in self.units])
    
    # destroy this group 
    def eliminate(self):
        for curr_unit in self.units:
            # kill any units left alive
            while curr_unit.is_alive():
                curr_unit.wound()
            self.owner.lose_unit(curr_unit)
        
        # remove group from visibility mask, hex, and owning player
        self.owner.get_mask().seer_removed(self.get_hex(), self.get_sight_range())
        self.curr_hex.remove_group(self)
        self.owner.remove_group(self)
        if self.get_site():
            self.get_site().delink_spawn(self)
            
    
    # this group is eliminated if no unit is left alive, remove it from hex and player
    def check_elimination(self, turn_start=False):
        # shuffle dead units to end 
        last_live = self.num_units() - 1
        while last_live > 0 and not self.units[last_live].is_alive():
            last_live -= 1
        
        i = 0
        while i < last_live:
            if not self.units[i].is_alive():
                self.move_unit(i, len(self.units) - 1)
                last_live -= 1
#                self.live_unit_count -= 1
            else:
                i += 1
                
        live_unit_count = 0
        for curr_unit in self.units:
            if curr_unit.is_alive():
                live_unit_count += 1
        self.live_unit_count = live_unit_count
        
        self.update_trait_effects(turn_start)
        
        if self.has_live_units():
            # there are still living units in this group
            return False
        
        self.eliminate()

        return True
    
    def get_sight_range(self):
        return GROUP_BASE_SIGHT + self.scout_bonus 
    
    def update_trait_effects(self, turn_start=False):
        if turn_start:
            # groups that start their turn with a pathfinder get extra moves
            pathfinder_bonus = self.get_highest_trait(trait.PATHFINDER)
            for curr_unit in self.units:
                curr_unit.moves_left += pathfinder_bonus
             
        # set move mode
        if self.has_trait(trait.ARMY_FLIGHT):  
            self.move_mode = move_mode.FLIGHT
        else:
            if all([curr_unit.has_trait(trait.FLIGHT) for curr_unit in self.units]):
                self.move_mode = move_mode.FLIGHT
            else:
                if self.curr_hex.hex_type.is_water():
                    self.move_mode = move_mode.NAVAL
                else:
                    self.move_mode = move_mode.FOOT
        
        if len(self.units) == 0:
            self.moves_left = 0
        else:
            self.moves_left = min([curr_unit.get_moves_left() for curr_unit in self.units])
        
        # groups that have a scout get the appropriate bonus
        old_scout_bonus = self.scout_bonus
        self.scout_bonus = self.get_highest_trait(trait.SCOUT)
        if self.scout_bonus != old_scout_bonus:
            self.owner.get_mask().visibility_changed(self.get_hex(), GROUP_BASE_SIGHT + old_scout_bonus,  self.get_sight_range())
        
        # groups with inspirational leader get the appropriate bonus
        inspiration = self.get_highest_trait(trait.INSPIRE)
        for curr_unit in self.units:
            if inspiration > 0 and curr_unit.is_alive() and curr_unit.is_army():
                curr_unit.set_trait(trait.INSPIRED, inspiration)
            else:
                curr_unit.remove_trait(trait.INSPIRED)
        
        # set hidden status of group
        if self.curr_hex.hex_type.is_forest() and all([curr_unit.has_trait(trait.STEALTH) and not curr_unit.has_fought_this_turn() for curr_unit in self.units]):
            self.set_trait(trait.HIDDEN, True)
        elif self.curr_hex.is_settled() and all([curr_unit.has_trait(trait.BLEND) and not curr_unit.has_fought_this_turn()  for curr_unit in self.units]):
            self.set_trait(trait.HIDDEN, True)
        else:
            self.reveal()
#            for curr_unit in self.units:
#                curr_unit.remove_trait(unit.HIDDEN)    
        
        # adjust armor based on site armor bonus, if applicable
        if self.curr_hex.has_site() and self.curr_hex.get_garrison() == self:
            armor_bonus = self.curr_hex.site.trait_value(site_upgrade.ARMOR)
        else:
            armor_bonus = 0
        for curr_unit in self.units:
            if curr_unit.is_alive():
                curr_unit.set_armor_bonus(armor_bonus)
                
                
#        self.adjust_diplo_income()
    
    def update_burn_state(self):
        # remove burning if group is in water
        if self.curr_hex.has_water():
            for curr_unit in self.units:
                curr_unit.remove_trait(trait.BURNING)
            
        # add burning if group is in fire
        if self.curr_hex.has_fire():
            self.set_trait(trait.BURNING, True)
    
    def summon_unit(self, summon_type):
        if self.is_full():
            return
        
        new_unit = unit.Unit(unit.unit_types_by_name[summon_type])
        new_unit.set_trait(trait.SUMMONED, 2)
        self.add_unit(new_unit, index = 0) # put summoned unit at front
    
    # strip hidden status from group - caused by entering combat or being spotted by another player's group
    def reveal(self):
        for curr_unit in self.units:
            curr_unit.remove_trait(trait.HIDDEN)
#        if self.curr_hex.get_hidden_group() == self:
#            assert (self.curr_hex.get_active_group() == None)
#            self.curr_hex.activate_hidden()

    def is_hidden(self):
        return all([curr_unit.has_trait(trait.HIDDEN) for curr_unit in self.units])
       
#    def end_turn(self):    
#        # move hidden group to hidden spot that other players won't be able to interact with it on their turn
#        if self.is_hidden():
#            if self.curr_hex.get_active_group() == self:
#                self.curr_hex.hide_active()    
    
    def trait_used(self, using_unit, used_trait):
        if used_trait == trait.RESTORE:
            # RESTORE heals one unit
            for curr_unit in self.units:
                if curr_unit.is_wounded():
                    curr_unit.heal()
                    break
    
    def start_turn(self, turn_number, hex_map):
#        self.fought_this_turn = False
        
        self.update_burn_state()
        
        # check for burning wounds
        for curr_unit in self.units:
            if curr_unit.has_trait(trait.BURNING):
                if curr_unit.is_alive() and random.random() < unit.BURN_WOUND_CHANCE:
                    curr_unit.wound()
                curr_unit.remove_trait(trait.BURNING)
        
        assert(self.owner != None)
        
        for curr_unit in self.units:
            curr_unit.start_turn(self.get_hex(), turn_number)
        
        # 'unsummon'/'rot' units whose countdown clock has expired
        i = 0
        while i < len(self.units):
            curr_unit = self.units[i]
            if curr_unit.has_trait(trait.SUMMONED) and curr_unit.trait_value(trait.SUMMONED) == 0:
                self.remove_unit(curr_unit)
            elif curr_unit.has_trait(trait.ROTTING) and curr_unit.trait_value(trait.ROTTING) == 0:
                self.remove_unit(curr_unit)
            else:
                i += 1
        
        # summon units, if applicable
        summons_needed = {}
        for curr_unit in self.units:
            if curr_unit.has_trait(trait.SUMMON) and curr_unit.is_alive():
                curr_count = summons_needed.get(curr_unit.trait_value(trait.SUMMON), 0)
                summons_needed[curr_unit.trait_value(trait.SUMMON)] = curr_count + 1
            if curr_unit.has_trait(trait.SUMMONED) and curr_unit.is_alive():
                curr_count = summons_needed.get(curr_unit.type_name, 0)
                summons_needed[curr_unit.type_name] = curr_count - 1
                
        for type_name in summons_needed:
            for i in range(summons_needed[type_name]):
                self.summon_unit(type_name)
        
        def suffer_unsupplied(unsupplied_unit):
            # most armies don't do well in the wilderness - wound them if they don't have supply 
            if (unsupplied_unit.is_army() and unsupplied_unit.is_alive() 
                and not unsupplied_unit.has_trait(trait.LIGHT) and not unsupplied_unit.has_trait(trait.PILLAGER)):
                        curr_unit.wound()
         
        if not self.curr_hex.is_settled() and not self.curr_hex.heals_unit():
            # if there's a supply unit, it takes the effects and no one else does
            supplied = False
            for curr_unit in self.units:
                if curr_unit.is_alive() and curr_unit.consume_trait(trait.SUPPLY):
                    supplied = True
                    break
            
            # otherwise every unit must suffer out of supply effects
            if not supplied:
                for curr_unit in self.units:
                    suffer_unsupplied(curr_unit)
        else:
            # refresh supplies
            for curr_unit in self.units:
                curr_unit.refresh_trait(trait.SUPPLY)
    
        if self.has_trait(trait.PILLAGER):
            self.curr_hex.pillage()
            
        if self.has_trait(trait.SPOT):
            spy_hexes = hex_map.get_hexes_in_radius(self.get_hex(), self.get_sight_range())
            for curr_hex in spy_hexes:
                curr_hex.spy_on()
        
        # at start of week, refresh RESTORE
        if turn_number.day == 1:
            for curr_unit in self.units:
                curr_unit.refresh_trait(trait.RESTORE)
        # make group active if it was hidden so that current player can manipulate it
#        if self.curr_hex.get_hidden_group() == self:
#            self.curr_hex.activate_hidden()
#        self.reveal()
        
   
#        self.adjust_diplo_income()
        
#        self.update_moves_and_visibility(True)
        self.check_elimination(True)

# don't eliminate hire groups
class HireGroup(Group):
    
    def remove_unit(self, unit_to_remove, transfer=False):
        self.units.remove(unit_to_remove)
        return unit_to_remove
    
    def add_unit(self, unit_to_add, index=None):
        self.do_add(unit_to_add, index)
 
WANDERING_RANGE = 3
WANDERING_AGGRESSION = 3

class ActiveAIGroup(Group):
    def __init__(self, owner, patrol_range, aggression_range, goal_funcs, constraint_funcs = []):
        super(ActiveAIGroup, self).__init__(owner)
        self.range = patrol_range
        self.aggression_range = aggression_range
        self.goal_funcs = goal_funcs
        self.constraint_funcs = constraint_funcs
     
    def initialize(self, start_hex):
        self.start_hex = start_hex
        
        # give group needed attributes
        move_trait = start_hex.hex_type.required_trait
        if move_trait != None:
            self.set_trait(move_trait, True)
        
        assert(start_hex.get_active_group() == None)
    
        self.set_hex(self.start_hex)
        self.start_hex.add_group(self)
    
    # Active AI groups are atomic.  Can never merge with other groups
    def can_merge(self, new_group):
        return False

    def get_center_hex(self):
        return self.start_hex
    
    def get_range(self):
        return self.range

    def get_aggression_range(self):
        return self.aggression_range
    
    def has_goal(self):
        return False
    
#    def get_ai(self):
#        return self.ai
    
    def get_goal_funcs(self):
        return self.goal_funcs
    
    def get_constraint_funcs(self):
        return self.constraint_funcs
        
class ZonePatrol(ActiveAIGroup):
    
    def __init__(self, site, patrol_range, aggression_range):
        self.site = site
        self.reputation_value = site.get_owner().patrol_reputation
        super(ZonePatrol, self).__init__(site.get_owner(), patrol_range, aggression_range, site.get_owner().get_goal_funcs(),
                                         constraint_funcs = player_type.zone_patrol_constraints)
        
    def get_site(self):
        return self.site
    
    def get_zone(self):
        return self.site.get_hex().get_zone()
        
    def get_level(self):
        return self.site.get_level()

class Wanderer(ActiveAIGroup):
    
    def __init__(self, site, range=WANDERING_RANGE, aggression = WANDERING_AGGRESSION):
        owner = site.get_owner()
        super(Wanderer, self).__init__(owner, range, aggression, owner.get_goal_funcs())
    
    def get_center_hex(self):
        return self.curr_hex   

class QuestingBeast(ActiveAIGroup):
    
    def __init__(self, owner):
        super(QuestingBeast, self).__init__(owner, 2, 0, owner.get_goal_funcs())
    
    def get_center_hex(self):
        return self.curr_hex  

class Assassin(ActiveAIGroup):
    
    def __init__(self, owner, target):
        super(Assassin, self).__init__(owner, WANDERING_RANGE, WANDERING_AGGRESSION, player_type.assassin_goals)
        self.target = target
    
    def get_center_hex(self):
        return self.curr_hex   
    
    def get_goal(self):
        if self.target.is_alive():
            return self.target.get_group().get_hex()
        
        return None


