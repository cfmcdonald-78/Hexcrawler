'''
Created on Jun 29, 2012

@author: Chris
'''
import gamemap.map_maker as map_maker
import gamemap.site_type as site_type, gamemap.mask as mask
import mob.unit as unit, mob.group as group, mob.item as item, mob.hero as hero
import player, player_type, random_event, combat, reputation
import random 
import core.event_manager as event_manager
from core.event_manager import Event
from collections import namedtuple


GameParams = namedtuple('GameParams', ['dimensions', 'seed', 'player_name'])

class Turn(object):
    
    def __init__(self, week, day):
        self.week = week
        self.day = day
    
    def increment(self):
        self.day += 1
        event_manager.queue_event(Event(event_manager.DAY_START, [self.week, self.day]))

        if self.day == 8:
            self.day = 1
            self.week += 1
            event_manager.queue_event(Event(event_manager.WEEK_START, [self.week]))  

class Game(object):
    '''
    classdocs
    '''
    def __init__(self, game_params):
        '''
        Constructor
        '''
        random.seed(game_params.seed)
      
        # create map
        hex_width, hex_height = game_params.dimensions
        map_generator = map_maker.ProceduralMapmaker(hex_width, hex_height)

        # keep creating maps until we find one that can be 'zoned' successfully
        reject_count = 0
        while True:
            self.hex_map = map_generator.generate()
            if self.hex_map.assign_zones():
                break
            reject_count += 1
            
        print "rejected " + str(reject_count) + " maps"
        
        # set up players 
        self.players = []
        self.npc_table = {}
        for npc_type in player_type.npc_player_types:
            npc_player = player.NPCPlayer(npc_type)
            self.npc_table[npc_type.name] = npc_player
            self.players.append(npc_player)

        human = player.Player(game_params.player_name, player.HUMAN, (0, 0, 200))
        self.players.append(human)
       
        
        # assign visibility masks to players
        for curr_player in self.players:
            curr_player.set_mask(mask.Mask(curr_player, self.hex_map))
        self.mask = human.get_mask()
        self.debug_mask = mask.Mask( human, self.hex_map, True)
        
        # populate map with sites
        self.hex_map.populate(self.npc_table)
        
        # find starting location
        start_zone = self.hex_map.get_start_zone()
        self.start_hex = self.hex_map.find_site("Rogue's Den", (1, 1), start_zone).get_hex()
        self.start_hex.site.transfer(human, conquered=False)  # player starts in control of Rogue's Den

        starting_party = group.Group(human)
        my_hero = hero.Hero(unit.unit_types_by_name["Classic Hero"])
        starting_party.add_unit(my_hero)
        starting_party.add_unit(unit.Unit(unit.unit_types_by_name["Warrior"]))
        starting_party.add_unit(unit.Unit(unit.unit_types_by_name["Bowman"]))
        self.start_hex.add_group(starting_party)
   
        # initialize settled area
        for curr_player in self.players:
            for curr_site in curr_player.get_sites():
                if curr_site.settles():
                    for i in range(3):
                        curr_site.spread_settlement(self.hex_map)
       
        random_event.seed_map(self.hex_map)
       
        self.curr_player_index = 0
        self.turn = Turn(1, 1)
        self.terminated = False
   
    def initialize(self, is_new_game):
        game_events = [event_manager.HERO_LOST, event_manager.SITE_LOOTED]
        event_manager.add_listener_multi(self.handle_event, game_events)
        
        if is_new_game:
            self.start_turn()
   
    def get_event_data(self):
        return self.event_data
    
    def remove_player(self, lost_player):
        lost_player_index = self.players.index(lost_player)
        self.players.remove(lost_player)
        if lost_player_index <= self.curr_player_index:
            self.curr_player_index -= 1
        if lost_player_index == self.curr_player_index:
            self.advance_turn()
    
    def handle_event(self, event):
        if event.type == event_manager.HERO_LOST:
            losing_player = event.data['player']
            if losing_player.is_actor() and losing_player.get_hero_count() == 0:
                # an active player loses the game upon losing his/her last hero
                event_manager.queue_event( Event(event_manager.PLAYER_LOST, [losing_player, losing_player.get_name() + " has no more heroes to champion the cause"]) )
                self.remove_player(losing_player)
            
        elif event.type == event_manager.SITE_LOOTED:
            looter = event.data['player']
            looted_site = event.data['site']
            
            # if a human player takes out a city-state or overlord's lair, he/she wins the game
            if looter.is_human() and (looted_site.get_type() == site_type.site_types["City-state"] or
                                      looted_site.get_type() == site_type.site_types["Overlord's Lair"]):
                event_manager.queue_event(Event(event_manager.PLAYER_WON, [looter, looter.get_name() + " has conquered " + looted_site.get_name()]))
            # if a monster player takes out a city-state, it wins the game
            elif looter.is_monster() and looted_site.get_type() == site_type.site_types["City-state"]:
                event_manager.queue_event(Event(event_manager.PLAYER_WON, [looter, looter.get_name() + " has conquered " + looted_site.get_name()]))                         

    def __setstate__(self, d):
        self.__dict__.update(d) 
        self.mask = self.get_curr_player().get_mask()
    
    def get_mask(self):
        return self.mask
    
    def handle_command(self, command):
        if self.terminated:
            # stop handling commands
            return False
        
        if command.validate(self):
            command.execute(self)
            return True
        
        return False
    
    def get_debug_mask(self):
        return self.debug_mask

    def start_turn(self):
        curr_player = self.get_curr_player()
        event_manager.queue_event(Event(event_manager.TURN_START, [curr_player, self.turn.week, self.turn.day]))
        curr_player.start_turn(self.turn, self)  
   
    def advance_turn(self):
        event_manager.queue_event(Event(event_manager.TURN_END, [self.get_curr_player(), self.turn.week, self.turn.day]))
        
        self.curr_player_index = (self.curr_player_index + 1) % len(self.players)
        if self.curr_player_index == 0:
            self.turn.increment()
            self.hex_map.day_start_update()
            random_event.check_for_event(self)
        
        self.start_turn()
        
    def get_turn(self):
        return self.turn
    
    def get_curr_player(self):
        return self.players[self.curr_player_index]
    
    def get_players(self):
        return self.players
    
    def get_map(self):
        return self.hex_map
    
    def get_start_hex(self):
        return self.start_hex

    # clean up state when closing game
    def do_cleanup(self):
        self.terminated = True
        combat.combat_locked_by = None

     