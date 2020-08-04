'''
Created on Jul 2, 2012

@author: Chris
'''
import thread, mob.group as group
from player_type import STARTING_GOLD, MONSTER, NEUTRAL, HUMAN
import player_type
import movement, reputation, income, fame
import core.process_manager as process_manager
import core.event_manager as event_manager
from core.event_manager import Event
from hexcrawl.misc_commands import EndTurnCommand
from gamemap.site import Site
from util.tools import linked_list_insert, linked_list_remove


def generic_hostility(ai_entity, hostility_table, value):
    level = ai_entity.get_level() - 1
    if isinstance(ai_entity, Site):
        level += 1
    
    return value < hostility_table[level]

# functions that determine if a particular faction group will act with hostility towards a particular active player

# friendliness of dead depends on how much killing player has done
def death_hostility(target_player, ai_entity, hostility_table):
    return generic_hostility(ai_entity, hostility_table, target_player.num_kills("Men"))

# friendliness of dwarf depends on how much income a player has
def cash_hostility(target_player, ai_entity, hostility_table):
    return generic_hostility(ai_entity, hostility_table, target_player.get_gold())

# friendliness of elves depends on how few sites a player possesses
def wildness_hostility(target_player, ai_entity, hostility_table):
    return  not generic_hostility(ai_entity, hostility_table, target_player.num_sites())

# chaos is always hostile
def always_hostility(target_player, ai_entity, hostility_table):
    return True

#  friendliness of men depends on reputation of player
def reputation_hostility(target_player, ai_entity, hostility_table):
    return generic_hostility(ai_entity, hostility_table, target_player.get_reputation())

hostility_funcs = {"death": death_hostility, "cash": cash_hostility, "wildness": wildness_hostility, 
                   "reputation": reputation_hostility, "always": always_hostility}

class Player(object):
    '''
    classdocs
    '''

    def __init__(self, name, base_type, color):
        '''
        Constructor
        '''
        self.actor = base_type == HUMAN  # is this player an active presence (human or AI) or just an obstacle (neutral/monster)
        if self.actor:
            self.gold = STARTING_GOLD  
            self.heroes = []  
        else:
            self.gold = 0
        
        self.heroes_granted = 0
        self.base_type = base_type

        self.color = color
        self.name = name
        self.patrol_reputation = 0
        self.kill_counts = {}  # per-player count of units killed
        self.initialize()
    
    def initialize(self):
        self.income = 0
        self.income_by_type = {}
        for income_type in income.INCOME_TYPES:
            self.income_by_type[income_type] = 0
            
        self.reputation_by_type = {}
        for rep_type in reputation.REPUTATION_TYPES:
            self.reputation_by_type[rep_type] = 0
    
        self.fame_by_type = {}
        for fame_type in fame.FAME_TYPES:
            self.fame_by_type[fame_type] = 0
    
        self.groups = []   
        self.sites = []    
      
        self.fame = 0
        self.reputation = 0
        self.num_heroes = 0
    
    def do_cleanup(self):
        self.initialize()
        
    # extreme recursion depth caused by circular list of groups and sites, so the pointers aren't
    # saved when saving them.  This code recreates the pointers on load.
    def __setstate__(self, d):
        self.__dict__.update(d) 
        def make_pointers(item_list):
            if len(item_list) > 0:
                for i in range(len(item_list)):
                    item_list[i].set_previous(item_list[i - 1]) # always works because -1 means end of list in Python
                    item_list[i].set_next(item_list[(i + 1) % len(item_list)])
        
        make_pointers(self.groups)
        make_pointers(self.sites)
        
    def set_mask(self, mask):
        self.mask = mask
    
    def num_heroes_granted(self):
        return self.heroes_granted
    
    def granted_hero(self):
        self.heroes_granted += 1
    
    def get_mask(self):
        return self.mask
    
    def is_human(self):
        return self.base_type == HUMAN
    
    def is_monster(self):
        return self.base_type == MONSTER
    
    def is_neutral(self):
        return self.base_type == NEUTRAL
    
    def is_actor(self):
        return self.actor
    
    def is_NPC(self):
        return False

    def num_sites(self):
        return len(self.sites)

    def add_kill(self, other_player):
        player_name = other_player.get_name()
        if player_name in self.kill_counts:
            self.kill_counts[player_name] += 1
        else: 
            self.kill_counts[player_name] = 1
        
    def num_kills(self, other_player_name):
        return self.kill_counts.get(other_player_name, 0)

    # entity is group or site which is target of query - is this entity hostile towards the other group?
    # by default this is always true - actors are hostile to everyone.  modified by AIPlayer
    def is_hostile(self, entity, other_player):
        return other_player != self
    
    def get_gold(self):
        return self.gold

    def get_color(self, entity, curr_player):
        if self.base_type == NEUTRAL:
            if self.is_hostile(entity, curr_player):
                return self.color[0]  # most hostile, site closed and patrols attack
            
            return self.color[1] # most friendly, site open
        return self.color
    
    def adjust_gold(self, delta_gold):
        # can't go below 0
        if self.gold + delta_gold < 0:
            delta_gold = -self.gold
        self.gold += delta_gold
        event_manager.queue_event(Event(event_manager.PLAYER_STATUS_CHANGE, [self, 'Gold', self.gold]))
        
    def adjust_income(self, delta_income, income_type):
        self.income += delta_income
        self.income_by_type[income_type] += delta_income
        event_manager.queue_event(Event(event_manager.PLAYER_STATUS_CHANGE, [self, 'Income', self.income]))
        
    def get_income(self):
        return self.income
    
    def get_reputation(self):
        return self.reputation
    
    def adjust_reputation(self, delta_reputation, reputation_type):
        self.reputation += delta_reputation
        self.reputation_by_type[reputation_type] += delta_reputation
        event_manager.queue_event(Event(event_manager.PLAYER_STATUS_CHANGE, [self, 'Reputation', self.reputation]))
    
    def get_fame(self):
        return self.fame
    
    def adjust_fame(self, delta_fame, fame_type):
        self.fame += delta_fame
        self.fame_by_type[fame_type] += delta_fame
        event_manager.queue_event(Event(event_manager.PLAYER_STATUS_CHANGE, [self, 'Fame', self.fame]))
    
    def get_name(self):
        return self.name
     
    def gain_unit(self, gained_unit):
        self.adjust_income(gained_unit.maintenance(), income.UNIT_MAINT)  
        reputation.adjust_reputation(reputation.GAINED_UNIT, gained_unit, self)
        
    def lose_unit(self, lost_unit):
        self.adjust_income(-lost_unit.maintenance(), income.UNIT_MAINT)  
        # reverse reputation adjustment done when unit gained, if any
        reputation.adjust_reputation(reputation.LOST_UNIT, lost_unit, self)
    
     
    def add_group(self, new_group):
        linked_list_insert(self.groups, new_group)
        self.groups.append(new_group)
        new_group.owner = self
    
    def remove_group(self, elim_group):
        linked_list_remove(self.groups, elim_group)
        self.groups.remove(elim_group)
        elim_group.owner = None

    def get_first_group(self):
        if len(self.groups) > 0:
            return self.groups[0]
        else:
            return None
        
    def get_first_site(self):
        if len(self.sites) > 0:
            return self.sites[0]
        else:
            return None
        
    def get_last_site(self):
        if len(self.sites) > 0:
            return self.sites[-1]
        else:
            return None
    
    def get_last_group(self):
        if len(self.groups) > 0:
            return self.groups[-1]
        else:
            return None
    
    def get_sites(self):
        return self.sites
    
    def add_site(self, site):
        linked_list_insert(self.sites, site)
        self.sites.append(site)
        self.adjust_income(site.get_income(), income.SITE_INCOME)
        site.owner = self
        self.get_mask().seer_added(site.get_hex(), site.get_sight_range())
        
    def remove_site(self, site):
        linked_list_remove(self.sites, site)
        self.sites.remove(site)
        self.adjust_income(-site.get_income(), income.SITE_INCOME)
        site.owner = None
        self.get_mask().seer_removed(site.get_hex(), site.get_sight_range())
    
    def start_turn(self, turn, curr_game):
        # check for deletion, since groups/sites can be lost due to death/revolt
        i = 0
        while i < len(self.groups):
            curr_group = self.groups[i]
            curr_group.start_turn(turn, curr_game.hex_map)
            if i < len(self.groups) and curr_group == self.groups[i]:
                i += 1
        
        i = 0        
        while i < len(self.sites):
            curr_site = self.sites[i]      
            curr_site.start_turn(turn, curr_game.hex_map)
            if i < len(self.sites) and curr_site == self.sites[i]:
                i += 1
        
        # player earns income at start of week
        if turn.day == 1:
            self.adjust_gold(self.get_income())

    def add_hero(self, new_hero):
        self.heroes.append(new_hero) 
       
        event_manager.queue_event(Event(event_manager.HERO_GAINED, [self]))
    
    def remove_hero(self, lost_hero):
        self.heroes.remove(lost_hero) 
        event_manager.queue_event(Event(event_manager.HERO_LOST, [self]))
    
    def get_hero_count(self):
        return len(self.heroes)
    
    def get_heroes(self):
        return self.heroes
    
class NPCPlayer(Player):
    
    def __init__(self, assigned_type):
        super(NPCPlayer, self).__init__(assigned_type.name, assigned_type.base_type, assigned_type.color)
        self.human = False
        self.site_patrols = {}
        self.active_group_goal_funcs = player_type.active_group_goal_funcs[assigned_type.patrol_func_name]
        self.patrol_reputation = assigned_type.patrol_reputation
        self.hostile_to = assigned_type.hostile_to
        self.hostility_func = hostility_funcs[assigned_type.hostility_func_name]
        self.hostility_table = assigned_type.hostility_table
    
    def get_goal_funcs(self):
        return self.active_group_goal_funcs
    
    # entity is group or site which is target of query - is this entity hostile towards the other group?
    def is_hostile(self, entity, other_player):
        if other_player.is_actor():
            # for actors, hostility is conditional on actor state
            return self.hostility_func(other_player, entity, self.hostility_table)
     
        # for non-actors, hostility is fixed - this NPC player either is or isn't hostile to a given other NPC player
        return other_player.get_name() in self.hostile_to
    
    def start_turn(self, turn, curr_game):
        print "starting turn of " + self.name
        super(NPCPlayer, self).start_turn(turn, curr_game)    

        thread.start_new_thread(self.ai, (curr_game, ))
                    
    def remove_group(self, elim_group):
        super(NPCPlayer, self).remove_group(elim_group)    
        if isinstance(elim_group, group.ZonePatrol):
            del self.site_patrols[elim_group.get_site()]
    
    def move_active_groups(self, curr_game):
       
        active_groups = [curr_group for curr_group in self.groups if isinstance(curr_group, group.ActiveAIGroup)]
  
        # keep going until every group has finished its business
        while True:
            process_manager.get_activity_lock()
            dest_group = {}
            for active_group in active_groups:
                active_group.done = True
                
                hexes_in_range = curr_game.get_map().get_hexes_in_radius(active_group.get_center_hex(), active_group.get_range())
                dest = player_type.move_active_group(active_group, dest_group, hexes_in_range, self.get_mask())
               
                if dest != None:
                    dest_group[dest] = active_group
                    curr_game.handle_command(movement.MoveCommand(active_group.get_hex(), dest))
            
            # release lock so process manager can do updates based on newly issued commands, wait for process
            # manager to finish its business before continuing
            process_manager.release_activity_lock()
            process_manager.wait_for_quiet()   
            active_groups = [active_group for active_group in active_groups if (not active_group.done) and active_group.is_active()]
            if len(active_groups) == 0:
                break
    
    def ai(self, curr_game):
        self.move_active_groups(curr_game)
        assert(len(process_manager.process_list) == 0)
        
        # spawn new patrols at end of turn
        for curr_site in self.sites:  
            # non-actors throw out patrols rather than actively taking over the map
            if (not self.is_actor() and curr_site.is_active() and curr_site not in self.site_patrols
                and curr_site.hex_loc.get_active_group() == None):
                
                spawn_hex = curr_game.get_map().get_spawn_hex(curr_site.hex_loc)
                if spawn_hex != None:
                    new_group = curr_site.spawn_group()
                    if new_group != None:
#                    new_patrol.set_reputation_value(curr_site.get_level() * self.patrol_reputation)
                        new_group.initialize(spawn_hex)
                        
                        if isinstance(new_group, group.ZonePatrol):
                            # make sure each site only has one  patrol at at time
                            self.site_patrols[curr_site] = new_group
        
        event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [EndTurnCommand(self)]))
