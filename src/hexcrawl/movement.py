'''
Created on Jun 30, 2012

@author: Chris
'''
import gamemap.hexgrid as hexgrid, gamemap.mask as mask
from heapq import heappush, heappop
import core.process_manager as process_manager, core.command as command, core.event_manager as event_manager
from core.process_manager import StepProcess
from core.event_manager import Event
import combat, loot
import mob.trait as trait
import gamemap.site_upgrade as site_upgrade

MOVE_UPDATE_DELAY = 150
MOVE_DONE = True
MOVE_NOT_DONE = False

class MoveCommand(command.Command):
    
    def __init__(self, start_loc, goal_loc):
        self.start_loc = start_loc
        self.goal_loc = goal_loc
        
    def validate(self, game):
        move_group = game.get_map().get_hex(self.start_loc.x, self.start_loc.y).active_group
        
        return move_group != None and move_group.get_owner() == game.get_curr_player()
        # TODO: validate hex location of start and end, validate player owns group being moved

    def execute(self, game):
        hex_map = game.get_map()
        move_group = hex_map.get_hex(self.start_loc.x, self.start_loc.y).active_group
        move_goal = hex_map.get_hex(self.goal_loc.x, self.goal_loc.y)
        
        human_visible = False
        for player in game.get_players():
            if player.is_human():
                if player.get_mask().get_visibility(self.goal_loc.x, self.goal_loc.y) == mask.VISIBLE:
                    human_visible = True
                    break
        
        process_manager.attach_process(MoveProcess(move_group, move_goal, hex_map, human_visible))

class MoveProcess(StepProcess):

    def __init__(self, group, goal, hex_map, human_visible):
        super(MoveProcess, self).__init__(MOVE_UPDATE_DELAY, human_visible)
    
        self.group = group
        self.path_index = 0
        self.path = None
        self.goal = goal
        self.hex_map = hex_map
        self.start = self.group.curr_hex
#        self.taken_site_fire = False
        
        self.generate_path()

    # use A* search to find path to goal hex
    def generate_path(self):
        reach_cost = {}
        predecessor = {}
        open_hexes = []
        closed_hexes = set([]) 

        reach_cost[self.start] = 0
        heappush(open_hexes, (hexgrid.get_distance(self.start, self.goal), self.start))
        
        while len(open_hexes) > 0:
            (curr_cost, curr_hex) = heappop(open_hexes)
            closed_hexes.add(curr_hex)
                
            # stop if we reach goal
            if curr_hex == self.goal:
                break
            
            if curr_hex.is_blocked(self.group):
                # can't move through a hex with other forces
                neighbors = []
            else:
                neighbors = self.hex_map.get_neighbors(curr_hex.x, curr_hex.y) 
                 
            for neighbor in neighbors:
              
                if neighbor in closed_hexes:
                    continue
                
                # only put an illegal hex on the path if it's the goal - then we can walk up to it but not get there
                if not neighbor.legal_move(self.group) and (not neighbor == self.goal):
#                if not neighbor.legal_move(self.group, neighbor == self.goal):
                    continue
                
                new_cost = reach_cost[curr_hex] + curr_hex.get_move_cost(self.group, neighbor)
                      
                if (neighbor not in reach_cost) or (new_cost < reach_cost[neighbor]):
                    reach_cost[neighbor] = new_cost
                    predecessor[neighbor] = curr_hex
                    heappush(open_hexes, (new_cost + hexgrid.get_distance(neighbor, self.goal), neighbor)) 
        
        self.path = []
         
        if curr_hex != self.goal:
            return
         
        while curr_hex != self.start:
            self.path.insert(0, curr_hex)
            curr_hex = predecessor[curr_hex]

    
    def get_next_hex(self):
        if self.path_index == len(self.path):
            return None
        return self.path[self.path_index]
    
    def get_curr_hex(self):
        return self.group.curr_hex
    
    def on_abort(self):
        self.finish()
        
    def on_fail(self):
        self.finish()
    
    def on_success(self):
        self.finish()
    
    def finish(self):
        event_manager.queue_event(Event(event_manager.MOVE_DONE, [self.group, self.start, self.get_curr_hex()]))
  
    def next_step(self):
        if self.path_index == len(self.path):
            self.succeed()
            return self.finish()
        
        next_hex = self.get_next_hex() 
        self.do_next_step(next_hex) 
    
    def do_next_step(self, next_hex):
        self.group.done = True # for patrols - gives them a chance to attack repeatedly if they get up to a foe.  See AI code

        move_cost = self.group.curr_hex.get_move_cost(self.group, next_hex) # + (1 if storm_penalty > 0 else 0)
        if move_cost > self.group.get_moves_left():
            self.fail()
            return
        
        if not next_hex.legal_move(self.group):
            self.abort()
            return # can happen on AI turn when another AI's move gets in the way of this one's plans
        
        if next_hex.will_fight(self.group.get_owner()):
            assert(self.path_index == len(self.path) - 1)
            self.group.done = False # for patrols - gives them a chance to attack repeatedly if they get up to a foe.  See AI code
            self.pause()
            if next_hex.has_site() and next_hex.site.has_trait(site_upgrade.MAP_ATTACK):
                # do a MapAttack followed by combat
                map_attack_process = combat.MapAttackProcess(next_hex, self.group, self.human_visible, paused_movement=self)
                map_attack_process.attach_child(combat.CombatProcess(self, self.human_visible, self.hex_map))
                process_manager.attach_process(map_attack_process)
            else:
                process_manager.attach_process(combat.CombatProcess(self, self.human_visible, self.hex_map))
            return 
        
        
        if next_hex.has_lootable_site(self.group):

            loot.do_loot(next_hex, self.group)
        self.group.move(next_hex, move_cost)
      
        if next_hex.has_storm(): # moving into a storm causes restrained state
            self.group.set_trait(trait.RESTRAINED, next_hex.get_storm_penalty())
        
        self.path_index += 1
        
        if self.path_index == len(self.path):
            self.succeed()
            return 
      