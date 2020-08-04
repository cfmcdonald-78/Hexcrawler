'''
Created on Jun 27, 2012

@author: Chris
'''
import mob.unit as unit, mob.group as group
import  hexcrawl.income as income
import site_type, site_upgrade
import random
import core.event_manager as event_manager
from core.event_manager import Event
from util.tools import DoublyLinkedObject
#from file.data_loader import DataLoader

HIRE_SIZE = 6
SITE_BASE_SIGHT = 1
REVOLT_STRENGTH = 3

class Site(DoublyLinkedObject):
    '''
    classdocs
    '''
    def __init__(self, hex_loc, new_site_type, level, owner, default_owner=None):
        super(Site, self).__init__()
        self.hex_loc = hex_loc
        self.site_type = new_site_type
        self.name = new_site_type.gen_name()
        self.level = level
        self.for_hire = None # units/characters available for hire in this hex
        self.builder = owner
        if default_owner == None:
            self.default_owner = owner
        else:
            self.default_owner = default_owner
            
        self.owner = owner
        self.fixed_prisoner = None
        self.embassy_player = None
        self.upgrades = []
        self.upgrade_traits = {}
        self.next = self.previous = None  # sites are on doubly-linked circular list, pointers set in player.add_site()
        
        self.income = 0 
        owner.add_site(self)
        self.status = site_type.ACTIVE
        if self.site_type.loot_effects != None:
            self.base_gold = self.level * self.site_type.loot_effects.gold

        self.for_hire = group.HireGroup(None)
      
        if self.site_type.garrison_info != None:
            self.garrison_size = random.randint(self.site_type.garrison_info.min, self.site_type.garrison_info.max)
            self.base_gold *= self.garrison_size
        else:
            self.garrison_size = 0
        
        self.make_site_group()
        self.fill_for_hire_units()
        
    def get_sight_range(self):
        return SITE_BASE_SIGHT + self.trait_value(site_upgrade.SIGHT)

    def set_prisoner(self, prisoner_unit):
        self.fixed_prisoner = prisoner_unit

    def get_fixed_prisoner(self):
        return self.fixed_prisoner
    
    def set_embassy(self, new_embassy_player):
        prev_embassy_player = self.embassy_player
        diplo_income = int(unit.DIPLOMAT_FRACTION * self.income)
        if prev_embassy_player != None:
            prev_embassy_player.adjust_income(-diplo_income, income.DIPLOMAT_INCOME)
        if new_embassy_player != None:
            new_embassy_player.adjust_income(diplo_income, income.DIPLOMAT_INCOME)

        self.embassy_player = new_embassy_player
    
    def get_embassy(self):
        return self.embassy_player
    
    def get_upgrades(self):
        return self.upgrades
    
    def get_settle_range(self):
        return self.site_type.settle_effect + self.trait_value(site_upgrade.SETTLE)
    
    def add_upgrade(self, new_upgrade_name):
        assert(new_upgrade_name not in self.upgrades)
        self.upgrades.append(new_upgrade_name)
        
        new_upgrade = site_upgrade.upgrades_by_name[new_upgrade_name]
        for trait in new_upgrade.effects:
            if self.has_trait(trait):
                self.upgrade_traits[trait] = self.trait_value(trait) + new_upgrade.effects[trait]
            else:
                self.upgrade_traits[trait] = new_upgrade.effects[trait]
                
    def remove_upgrade(self, old_upgrade_name):
        self.upgrades.remove(old_upgrade_name)
        
        old_upgrade = site_upgrade.upgrades_by_name[old_upgrade_name]
        for trait in old_upgrade.effects:
            if self.trait_value(trait) != old_upgrade.effects[trait]:
                self.upgrade_traits[trait] = self.trait_value(trait) - old_upgrade.effects[trait]
            else:
                del self.upgrade_traits[trait]
    
    def has_trait(self, trait):
        return trait in self.upgrade_traits
    
    def trait_value(self, trait):
        return self.upgrade_traits.get(trait, 0)

    def sack(self):
        self.owner.remove_site(self)
        self.owner = self.default_owner
        self.owner.add_site(self)
        self.status = site_type.SACKED
        self.empty_for_hire()
        self.set_embassy(None)
        self.fixed_prisoner = None
        
        for upgrade in self.upgrades:
            self.remove_upgrade(upgrade)
    
    def destroy(self):
        self.owner.remove_site(self)
        self.hex_loc.remove_site(self)
        self.set_embassy(None)
        self.fixed_prisoner = None
        self.empty_for_hire()
        
    def transfer(self, new_owner, conquered=True):
        self.set_embassy(None)
        self.fixed_prisoner = None
        self.owner.remove_site(self)
        new_owner.add_site(self)
        if conquered:
            self.empty_for_hire()

    def get_owner(self):
        return self.owner
    
    def is_occupied(self):
        return self.is_active() and self.owner != self.default_owner and self.garrison_size > 0
    
    def get_type(self):
        return self.site_type
    
    def fill_site_group(self, new_group):
        for new_unit_type in self.group_unit_types:
            new_group.add_unit(unit.Unit(new_unit_type))
        return new_group 
    
    # make group used for garrison and patrols
    def make_site_group(self):
        self.group_unit_types = []
        if self.garrison_size == 0 or self.owner.is_actor():
            # active players don't get a free ride, have to fill their own  garrison
            return

        garrison_info = self.site_type.garrison_info

        candidates = self.site_type.garrison_candidates(self.level)
        
        for i in range(self.garrison_size):
            self.group_unit_types.append(random.choice(candidates))
        
        has_leader = random.random() <= garrison_info.leader_chance
        leader_candidates = self.site_type.leader_units.get(self.level, [])
        if has_leader and len(leader_candidates) > 0:
            self.group_unit_types.append(random.choice(leader_candidates))
    
        # fill in garrison  
        self.hex_loc.add_garrison(self.fill_site_group(group.Group(self.owner)))
    
    def refresh_garrison(self):
        if not self.is_active() or self.owner.is_actor() or self.garrison_size == 0:
            # active players don't get a free ride, have to fill their own  garrison
            return
        
        garrison = self.hex_loc.get_garrison()
        if garrison != None:
            garrison.clear_dead_units()
        else:
            garrison = group.Group(self.owner)
            self.hex_loc.add_garrison(garrison)
            
        # add one new unit if there's room
        if garrison.num_units() < len(self.group_unit_types):
            self.add_garrison_unit()
            
    def add_garrison_unit(self):
        garrison = self.hex_loc.get_garrison()
        
        for i in range(len(self.group_unit_types)):
            if i >= garrison.num_units() or not garrison.get_unit(i).is_alive():
                garrison.add_unit(unit.Unit(self.group_unit_types[i]))
                return
            
            desired_unit_name = self.group_unit_types[i].name
            actual_unit_name = garrison.get_unit(i).get_name()
            if desired_unit_name != actual_unit_name:
                garrison.add_unit(unit.Unit(self.group_unit_types[i]), index = i)
                return
    
    def empty_for_hire(self):
        self.for_hire = group.HireGroup(None)
    
    def fill_for_hire_units(self):
        if self.owner.is_monster():
            return

        curr_candidates = self.site_type.get_units(self.level, True)
        for i in range(HIRE_SIZE):
            unit_type = random.choice(curr_candidates)
            self.for_hire.add_unit(unit.Unit(unit_type))
            if i >= (HIRE_SIZE / 2 - 1):
                curr_candidates = self.site_type.get_units(self.level, False)
        
        non_combatants = self.site_type.get_non_combatants(self.level)
        if len(non_combatants) > 0:
            self.for_hire.add_unit(unit.Unit(random.choice(non_combatants)))
        self.for_hire.add_unit(unit.Unit(unit.unit_types_by_name["Supply Wagon"]))
    
    def add_for_hire(self, new_unit):
        is_army = new_unit.is_army()
        
        num_armies = [curr_unit.is_army() for curr_unit in self.for_hire.units].count(True) - 1 # subtract one for the wagon
        num_chars =  self.for_hire.num_units() - 1 - num_armies
        
        target_index = 0 if is_army else num_armies
        
        if self.for_hire.num_units() == group.MAX_UNITS:
            self.for_hire.remove_unit_at_index(target_index)
        
        self.for_hire.add_unit(new_unit, index=target_index)
        
    
    # add a supply wagon (if there isn't one), a non_combatant (if there isn't one), and one each of armies and characters, 
    # as long as each isn't over its limit
    def refresh_for_hire_units(self):
        if self.owner.is_monster():
            return
        
        if self.for_hire.num_units() == group.MAX_UNITS:
            return
        
        has_wagon = any([curr_unit.type_name == "Supply Wagon" for curr_unit in self.for_hire.units])
        
        if not has_wagon:
            self.for_hire.add_unit(unit.Unit(unit.unit_types_by_name["Supply Wagon"]))
         
        num_armies = [curr_unit.is_army() for curr_unit in self.for_hire.units].count(True) - 1 # subtract one for the wagon
        num_chars =  self.for_hire.num_units() - 1 - num_armies
        
        last_char_index = num_armies + num_chars - 1
        last_char_unit = self.for_hire.get_unit(last_char_index)
        if last_char_unit == None or last_char_unit.is_combatant():
            # need to add a non-combatant
            non_combatants = self.site_type.get_non_combatants(self.level)
            if len(non_combatants) > 0:
                self.for_hire.add_unit(unit.Unit(random.choice(non_combatants)), index=last_char_index + 1)
        else:
            num_chars -= 1
        
        for i in range(1 + self.trait_value(site_upgrade.RECRUIT)):
            if num_armies < HIRE_SIZE/2:
                new_unit = unit.Unit(random.choice(self.site_type.get_units(self.level, True)))
                self.for_hire.add_unit(new_unit, index=num_armies)
                num_armies += 1
            if num_chars < HIRE_SIZE/2:
                new_unit = unit.Unit(random.choice(self.site_type.get_units(self.level, False)))
                self.for_hire.add_unit(new_unit, index=num_armies + num_chars)
                num_chars += 1
            
    def hireable_by(self, hiring_player):
        if self.status == site_type.SACKED or self.for_hire == None:
            return False
        
        active_group = self.hex_loc.get_active_group()
        hirer_present = active_group != None and active_group.get_owner() == hiring_player
        return hiring_player.is_actor() and (hiring_player == self.owner or hirer_present)
    
    def hire(self, hiring_player, hire_index):
        if self.for_hire == None or hire_index < 0 or hire_index >= self.for_hire.num_units() or not self.hireable_by(hiring_player):
            raise ValueError("Attempted impossible hire action")
        
        active_group = self.hex_loc.get_active_group()
        if active_group != None and active_group.is_full():
            return False  # active group already full, can't hire
        
        unit_for_hire = self.for_hire.get_unit(hire_index)
        hire_cost = unit_for_hire.hire_cost(active_group)
        if hiring_player.get_gold() < hire_cost:
            return False  # player too poor to hire this one
        
        will_join, reason = unit_for_hire.will_join(hiring_player)
        
        if not will_join:
            return False

        #expend gold, adjust reputation if needed, and make transfer
        hiring_player.adjust_gold(-hire_cost)
       
        if active_group != None:
            active_group.add_unit(unit_for_hire)
        else:
            new_group = group.Group(hiring_player)
            new_group.add_unit(unit_for_hire)
            self.hex_loc.add_group(new_group) 
            
        self.for_hire.remove_unit(unit_for_hire)
        
        return True 
    
    def get_units_for_hire(self):
        return self.for_hire
    
    def get_hex(self):
        return self.hex_loc
    
    def get_name(self):
        return self.name
    
    def get_level(self):
        return self.level
    
    def is_lootable(self, group):
        return (not self.hex_loc.has_garrison() and self.site_type.loot_effects != None 
                and self.is_active() and group.get_owner() != self.owner)
    
    def is_haven(self):
        return self.site_type.haven
    
    def is_tight_quarters(self):
        # armies can't fight in the cramped conditions of small sites garrisoned by characters.  (e.g. dungeons)
        return self.site_type.tight_quarters
    
    def is_active(self):
        return self.status == site_type.ACTIVE #or site_type.OWNED in self.status
    
    # return true if site is hostile towards acting group
    def is_hostile(self, other_player):
        return self.get_owner().is_hostile(self, other_player)

    def spawn_group(self):
        spawn_info = self.site_type.spawn_info
        if spawn_info == None or random.random() > spawn_info.chance_per_day:
            return None
    
        # compute aggression range
        aggression_range = self.site_type.aggression_range_func(self)
    
        if spawn_info.type == site_type.ZONE_PATROL:
            spawned = group.ZonePatrol(self, spawn_info.range, aggression_range)
        elif spawn_info.type == site_type.WANDERER:
            spawned = group.Wanderer(self.get_owner(), spawn_info.range, aggression_range)
        else:
            assert (False)
        
        if spawn_info.units == None:
            # copy garrison units to form spawn group
            self.fill_site_group(spawned)
        else:
            for unit_type_name in spawn_info.units:
                spawned.add_unit(unit.Unit(unit.unit_types_by_name[unit_type_name]))
        
        # give group needed attributes
        move_trait = self.hex_loc.hex_type.required_trait
        if move_trait != None:
            spawned.set_trait(move_trait, True)
        
        return spawned 
    
    def sacked(self):
        return self.status == site_type.SACKED
    
    def pillages(self):
        return self.is_active() and self.site_type.settle_effect < 0
    
    def settles(self):
        return self.site_type.settle_effect > 0
    
    def adjust_income(self, hex_map):
        old_income = self.income
        
        self.income = self.site_type.income_func(hex_map, self) #int(self.base_income * hex_map.count_settled_hexes(self.hex_loc, self.site_type.settle_effect) )
        if self.has_trait(site_upgrade.INCOME_BONUS):
            # each point of INCOME_BONUS is a 10% increase to income
            self.income += int(0.1 * self.trait_value(site_upgrade.INCOME_BONUS) * self.income) 
        
        self.owner.adjust_income(self.income - old_income, income.SITE_INCOME)
        
        if self.embassy_player != None:
            self.embassy_player.adjust_income(int(unit.DIPLOMAT_FRACTION * self.income) - int(unit.DIPLOMAT_FRACTION * old_income), 
                                          income.DIPLOMAT_INCOME)
    
    def get_income(self):
        return self.income
    
    def spread_settlement(self, hex_map):
        # if this is an active or owned settlement generator, attempt to spread settlement 
        if self.settles() and self.is_active():
            hex_map.spread_settlement(self.hex_loc, self.get_settle_range())
        
        self.adjust_income(hex_map)

    def revolt_chance(self):
        if not self.is_occupied() or not self.default_owner.is_hostile(self, self.get_owner()):
            return 0
        
        if self.owner == self.builder:
            return 0
        
        site_hex = self.get_hex()
        garrison = site_hex.get_garrison()
        if garrison == None:
            return 1
        else:
            sum_levels = 0
            for i in range(garrison.num_units()):
                if garrison.get_unit(i).is_army() or not self.site_type.garrison_info.is_army:
                    sum_levels += garrison.get_unit(i).get_level()
                revolt_strength = max(0, REVOLT_STRENGTH + self.trait_value(site_upgrade.REVOLT_STRENGTH))
                if revolt_strength == 0:
                    revolt_chance = 0
                else:
                    revolt_chance = 1 - (sum_levels / float(self.get_level() * revolt_strength))
                if revolt_chance < 0:
                    revolt_chance = 0
        
        return revolt_chance

    def garrison_depth(self):
        return 0 if self.site_type.garrison_info == None else self.site_type.garrison_info.depth

    # a site not controlled by its original owner and that site is hostile to owner [based on relevant 
    # criteria in site.is_hostile()] attempts to rise up.  Auto-fail if sum of levels of armies in garrison >= 3x level of site
    # otherwise proportional chance based on smallness of garrison r
    # if successful, garrison destroyed, any active group is displaced, and control reverts to original owner.
    def check_revolt(self, hex_map):
        if random.random() >= self.revolt_chance():
            return False
        
        print self.get_name() + "Revolting!"
        site_hex = self.get_hex()
        
        # revolt happened
        if site_hex.get_garrison() != None:
            site_hex.get_garrison().eliminate()
        
        active_group = site_hex.get_active_group()
        if active_group != None:
            open_neighbors = [neighbor for neighbor in hex_map.get_neighbors(site_hex.x, site_hex.y) if neighbor.legal_move(active_group)]
            if len(open_neighbors) == 0:
                active_group.eliminate()
            else:
                active_group.move(random.choice(open_neighbors), 0)
    
        # transfer site to new owner
        old_owner = self.get_owner()
        self.transfer(self.default_owner)
    
        event_manager.queue_event(Event(event_manager.SITE_REVOLT, [self, old_owner]))
        return True

    def start_turn(self, turn, hex_map):
    
        if self.get_owner().is_actor():
            print "starting turn of " + self.get_name()
        # a few special things happen at start of week
        if turn.day == 1:
            # check for revolt
            self.check_revolt(hex_map)
            
            # if garrison not full, grow it at start of week.
            self.refresh_garrison()
            
            # if units can be hired here, refresh available units at start of week
            self.refresh_for_hire_units()
#           
            self.spread_settlement(hex_map)
        
        if self.is_active():         
            self.adjust_income(hex_map)
        
        if self.status == site_type.ACTIVE and self.has_trait(site_upgrade.SPOT):
            spy_hexes = hex_map.get_hexes_in_radius(self.get_hex(), self.get_sight_range())
            for curr_hex in spy_hexes:
                curr_hex.spy_on()
     
        #if location is sacked, chance to return to active status
        if self.status == site_type.SACKED:
            if random.random() < self.site_type.reactivate_chance and self.hex_loc.get_active_group() == None:
                self.status = site_type.ACTIVE
                self.make_site_group()
                
        # if this is an active pillaging site, de-settle hexes under or adjacent it
        if self.status == site_type.ACTIVE and self.pillages():
            hex_map.pillage(self.hex_loc, 1)
