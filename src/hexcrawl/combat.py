'''
Created on Jun 30, 2012

@author: Chris
'''
import random, collections
import mob.unit as unit, mob.trait as trait, mob.group as group, mob.hero as hero, mob.item as item, reputation
#import activity
from core.process_manager import StepProcess
from core.event_manager import Event
import core.event_manager as event_manager
import gamemap.terrain as terrain
import gamemap.site_upgrade as site_upgrade
import gamemap.hexgrid as hexgrid
from math import ceil, atan
import core.options as options


combat_delay = {options.SLOW_COMBAT_SPEED: 1500, options.MED_COMBAT_SPEED: 750, options.FAST_COMBAT_SPEED: 375}
COMBAT_MOVE_COST = terrain.BASE_MOVE_COST # amount of MP it costs an attacker to attack if he doesn't successfully wipe out defenders

BASE_RETREAT_CHANCE = 0.25
CHAR_V_ARMY_RETREAT_MODIFIER = 0.5
FASTER_RETREAT_MODIFIER = 0.25

RANGED_COMBAT = "Ranged Combat"
HEAL = "Heal"
REVIVE = "Revive"
MELEE_COMBAT = "Melee Combat"
RETREAT = "Retreat"
phases = [RANGED_COMBAT, HEAL, REVIVE, MELEE_COMBAT, RETREAT]
phase_traits = {RANGED_COMBAT: trait.RANGED, HEAL: trait.HEAL, REVIVE:trait.REVIVE}

combat_locked_by = None  # serialize combat so that only one can occur at a time

class Force(object):
    
    def __init__(self, force_group):
        for curr_unit in force_group.units:
            curr_unit.fought() 
        
        self.name = force_group.get_owner().get_name()
        self.group = force_group
        self.index = -1
        self.strength = None
        self.ranged = None
        self.do_combat_start_effects()
#        self.win_penalty = 0
    
    def do_combat_start_effects(self):
        # compute Bloodthirst bonuses:
        for i in range(self.num_units()):
            curr_unit = self.get_unit(i)
            if curr_unit.is_alive() and curr_unit.has_trait(trait.BLOODTHIRST):
                blood_mult = 0
                adj_units = [self.get_unit(i - 1), self.get_unit(i + 1)]
                for adj_unit in adj_units:
                    if adj_unit != None and adj_unit.health == unit.WOUNDED:
                        blood_mult += 1
                if blood_mult > 0:
                    curr_unit.set_trait(trait.BLOOD_POWER, blood_mult * curr_unit.trait_value(trait.BLOODTHIRST))
    
    def next_unit(self):
#        self.win_penalty = 0
        self.index += 1
    
    def at_end(self):
        return self.index == self.num_units()
    
    def num_units(self):
        return self.group.num_units()
    
    def get_unit(self, index):
        return self.group.get_unit(index)
        
    def curr_unit(self):
        return self.group.get_unit(self.index)
    
    def prev_unit(self):
        if self.index == 0:
            return None
        return self.group.get_unit(self.index - 1)
    
    def add_kill(self, other_force):
        self.group.get_owner().add_kill(other_force.group.get_owner())
    
    def update_melee_strength(self):
        fighter = self.curr_unit()
        opponent = self.opponent.curr_unit()
        
        self.update_inspiration()

        if fighter == None or opponent == None:
            self.strength = None
            return

        new_strength = fighter.get_combat_strength(opponent)                                                                                         
        
        # add in bonus for following unit with GRANT STRENGTH ability
        next_unit = self.get_unit(self.index + 1)
        if next_unit != None and next_unit.is_alive():
            new_strength += next_unit.trait_value(trait.GRANT_STRENGTH)
        
        self.strength = new_strength
        
    def clear_temporary_traits(self):
        for i in range(self.group.num_units()):
            curr_unit = self.group.get_unit(i)
#            curr_unit.remove_trait(unit.INSPIRED)
            curr_unit.remove_trait(trait.EXHAUSTED)
            curr_unit.remove_trait(trait.BLOOD_POWER)
            
    def update_inspiration(self):
        inspiration = self.group.get_highest_trait(trait.INSPIRE)
        for i in range(self.group.num_units()):
            curr_unit = self.group.get_unit(i)
            if inspiration > 0 and curr_unit.is_alive() and curr_unit.is_army():
                curr_unit.set_trait(trait.INSPIRED, inspiration)
            else:
                curr_unit.remove_trait(trait.INSPIRED)
    
    def update_exhaustion(self, won):
        curr_unit = self.curr_unit()
        if won and not curr_unit.has_trait(trait.RELENTLESS):
            # strength depleted by repeated battles, up to maximum of 1/2 base strength
            new_exhausted = min (curr_unit.trait_value(trait.EXHAUSTED) + 1, curr_unit.get_raw_strength() / 2)
            curr_unit.set_trait(trait.EXHAUSTED, new_exhausted)
#        else:
#            curr_unit.remove_trait(unit.EXHAUSTED)
    
    def get_strength(self, phase):
        curr_unit = self.curr_unit()
        if curr_unit == None:
            return None
        
        if phase == MELEE_COMBAT:
            if self.opponent.curr_unit() == None:
                return None
            return self.strength
        if phase == HEAL:
            return curr_unit.trait_value(trait.HEAL) if curr_unit.has_trait(trait.HEAL) else None
        elif phase == REVIVE:
            return curr_unit.trait_value(trait.REVIVE) if curr_unit.has_trait(trait.REVIVE) else None
        elif phase == RANGED_COMBAT:
            return self.ranged
            
def check_10_val(value):
    return random.randint(1, 10) <= value

def check_20_val(value):
    return random.randint(1, 20) <= value

# returns true if attack hit, false otherwise
def check_block(force, index):
    stalwart_defense = 0
        
    target = force.get_unit(index)
    if target == None or not target.is_alive():
        # not gonna be blocking!
        return None
    
    prev_unit = force.get_unit(index - 1)
    if prev_unit != None and prev_unit.has_trait(trait.STALWART) and prev_unit.is_alive():
        stalwart_defense = prev_unit.get_armor()
           
    armor = max(stalwart_defense, target.get_armor())
    
    attacker = force.opponent.curr_unit()
    armor -= attacker.trait_value(trait.PIERCE)
  
    # restrain target, if applicable
    if attacker.has_trait(trait.RESTRAIN):
            target.set_trait(trait.RESTRAINED, attacker.trait_value(trait.RESTRAIN))
  
    if not check_20_val(armor):
        if target.has_trait(trait.SWARM) and target.health == unit.WOUNDED:
            # look for other swarm unit to take wound instead of killing this one
            found_proxy = False
            for other_unit in force.group.units:
                if other_unit.has_trait(trait.SWARM) and other_unit.health == unit.HEALTHY:
                    other_unit.wound()
                    found_proxy = True
                    break
            if not found_proxy:
                target.wound()
        else:         
            target.wound()
        if attacker.has_trait(trait.VAMPIRIC) and attacker.health == unit.WOUNDED:
            attacker.heal()
        if check_10_val(attacker.trait_value(trait.BURN)) and target.is_alive():
            target.set_trait(trait.BURNING, True)
        
        if not target.is_alive():
            force.opponent.add_kill(force) 
        
        event_manager.queue_event(Event(event_manager.UNIT_HIT, [force.group, index]))
        return False
    else:
        event_manager.queue_event(Event(event_manager.UNIT_BLOCK, [force.group, index]))
        return True

# returns true if target available and attack hits, false otherwise
def ranged_attack(firers):
    firers.ranged = None
    firers.opponent.ranged = None
    firers.opponent.index = -1
    
    attacker = firers.curr_unit()
    
    target_index = -1
    if attacker.has_trait(trait.ASSASSIN):
        # special targeting rules, look for support unit closest to back of enemy group.
        # if none found, fall through to normal targeting rules
        target_index = firers.opponent.num_units() - 1
        while (target_index >= 0):
            candidate = firers.opponent.get_unit(target_index)
            if candidate.is_alive() and candidate.is_support() and attacker.get_ranged_strength(candidate) > 0:
                break
            target_index -= 1
  
    if target_index == -1:
        target_index = max(0, firers.index - 1) 

        # long range units can fire more than one slot ahead
        range = trait.MAX_RANGE if attacker.has_trait(trait.LONG_RANGE) else 1
        while (firers.index - target_index < range and target_index > 0 and 
                (firers.opponent.get_unit(target_index) == None or not firers.opponent.get_unit(target_index).is_alive())):
            target_index -= 1

    target = firers.opponent.get_unit(target_index)
   
    if target != None and target.is_alive():
        firers.opponent.index = target_index
        strength = attacker.get_ranged_strength(target)
        firers.ranged = strength
        event_manager.queue_event(Event(event_manager.RANGED_ATTACK, [firers.group, firers.index]))
        if check_20_val(strength):
            check_block(firers.opponent, target_index)
            
            # if hit, check for splash
            if attacker.has_trait(trait.SPLASH):
                splash_targets = [target_index - 1, target_index + 1]
                for splash_index in splash_targets:
                    splash_target = firers.opponent.get_unit(splash_index)
                    # if target is viable, and this unit has a positive ranged strength against it, it takes
                    # an attack and must block or be hit
                    if splash_target != None and splash_target.is_alive() and attacker.get_ranged_strength(splash_target) > 0:
                        check_block(firers.opponent, splash_index)
            return True
        
        return False
    return False

def do_heal(target):
    target.heal()
    
def do_revive(target):
    target.revive()

def heal_attempt(healers):
    return heal_or_revive(healers, trait.HEAL, do_heal, lambda candidate : candidate.health == unit.WOUNDED)

def revive_attempt(healers):
    return heal_or_revive(healers, trait.REVIVE, do_revive, lambda candidate: candidate.health == unit.DEAD)

  # returns true if at least one unit healed/revived, false otherwise
def heal_or_revive(healers, heal_trait, success_func, target_func):
    #target nearest valid unit, preferring unit toward front
    forward = healers.index - 1
    backward = healers.index + 1
    target_indices = []
    max_targets = 1
    while len(target_indices) < max_targets and (forward >= 0 or backward < healers.num_units()):
        if forward >= 0 and target_func(healers.get_unit(forward)):
            target_indices.append(forward)
        if len(target_indices) < max_targets and backward < healers.num_units() and target_func(healers.get_unit(backward)):
            target_indices.append(backward)
        backward += 1
        forward -= 1
        
    if len(target_indices) == 0:
        # no valid target
        return False

    death_aura = healers.group.get_highest_trait(trait.DEATH_AURA)
    death_aura = max(death_aura, healers.opponent.group.get_highest_trait(trait.DEATH_AURA))
    life_aura = healers.group.get_highest_trait(trait.LIFE_AURA)
    life_aura = max(life_aura, healers.opponent.group.get_highest_trait(trait.LIFE_AURA))
    
    heal_mod = life_aura - death_aura

    strength = healers.curr_unit().trait_value(heal_trait) + heal_mod
    event_manager.queue_event(Event(event_manager.HEAL_ATTEMPT, [healers.group, healers.index]))
    ret_val = False
    for index in target_indices:
        target = healers.get_unit(index)
        if check_10_val(strength):
            success_func(target)
            event_manager.queue_event(Event(event_manager.UNIT_HEAL, [healers.group, index]))
            ret_val = True
        
    return ret_val

def combat_move_cost(defense_hex):
    if defense_hex.has_site():
        added_cost = defense_hex.site.trait_value(site_upgrade.IMPEDE)
    else:
        added_cost = 0
    
    return COMBAT_MOVE_COST + added_cost

phase_funcs = {RANGED_COMBAT: ranged_attack, HEAL: heal_attempt, REVIVE: revive_attempt}

class CombatProcess(StepProcess):
    
    def __init__(self, move_process, human_visible, hex_map):
        self.defense_hex = move_process.get_next_hex()
        delay = combat_delay[options.curr_options.own_combat_speed]
        if not move_process.group.get_owner().is_human() and not self.defense_hex.get_defenders().get_owner().is_human():
            # speed up AI vs. AI combat
            delay /= 2
        
        super(CombatProcess, self).__init__(delay, human_visible)
        self.paused_movement = move_process  # resume movement if combat succeeds
        
        self.attackers_advance = False
        self.attackers = Force(move_process.group)
        self.defenders = Force(self.defense_hex.get_defenders())
        self.rounds_left = 1
        if self.defenders.group == self.defense_hex.get_garrison():
            self.rounds_left = self.defense_hex.site.garrison_depth()
        
        self.attackers.opponent = self.defenders
        self.defenders.opponent = self.attackers
        self.forces = [self.attackers, self.defenders]
        self.no_armies = not self.defense_hex.armies_can_fight()  # can't fight with armies in confined area
        self.hex_map = hex_map
        self.init_round()
    
    def init_round(self):
        self.phase_index = 0
        self.current_force = self.defenders
        self.defenders.index = -1
        self.attackers.index = -1
            
    def init(self):
        super(CombatProcess, self).init()
    
    def get_curr_hex(self):
        return self.defense_hex

    def is_unuseable(self, test_unit, trait = None):
        return not test_unit.is_alive() or (test_unit.is_army() and self.no_armies) or (trait != None and not test_unit.has_trait(trait))
    
    def skip_unusable_units(self, force, trait = None):
        # skip over dead units and those that can't fight here
        while not force.at_end() and self.is_unuseable(force.curr_unit(), trait):
            force.next_unit()
                                          
    # return true if done handling this special trait, false otherwise
    def handle_special(self, special_trait, special_func):
        self.current_force.next_unit()
        self.skip_unusable_units(self.current_force, special_trait)
        
        if self.current_force.at_end():
            print "special func done for current force"
            if self.current_force == self.defenders:
                # switch to attackers and restart function
                self.current_force = self.attackers
                self.attackers.index = -1
                return self.handle_special(special_trait, special_func)
            self.current_force = self.defenders
            self.attackers.index = -1
            self.defenders.index = -1
            return True

        print "Doing special func for " + special_trait + "on unit " + str(self.current_force.index)
        special_func(self.current_force)
        return False
      
    def victory_adjustments(self, win_group, lose_group, win_player, lose_player, loser_eliminated):
        reputation_adj = 0
        item_gained = None
        
        if loser_eliminated:
            # grant reputation to winner if it was an active player that defeated a monster army patrol of 
            # high enough level
            reputation_adj = reputation.adjust_reputation(reputation.DESTROYED_GROUP, lose_group, win_player)
            
            # if a lone hero kills a unit with the QUEST trait, grant him an item of level = level of monster
            if win_group.num_units() == 1 and isinstance(win_group.get_unit(0), hero.Hero):
                for unit_index in range(lose_group.num_units()):
                    curr_unit = lose_group.get_unit(unit_index)
                    
                    if curr_unit.has_trait(trait.QUEST):
                        item_gained = item.random_item(curr_unit.get_level())
                        win_group.add_item(item_gained)
        
        if reputation_adj != 0 or item_gained != None:
            event_manager.queue_event(Event(event_manager.COMBAT_SPOILS, [reputation_adj, item_gained]))
       
    def trial_of_strength(self):
        if self.attackers.strength <= 0 and self.defenders.strength <= 0:
            # avoid infinite loop if both strengths are <= 0 (due to army vs. non-army, restrained, or other penalties).
            # in this case both armies increment index without effect 
            return None, None
 
        def chance(diff):
            # scale atan to range from 0 to 1
            return 0.5 + 0.3183099 * atan(diff/2.0)
 
        if self.attackers.strength <= 0:
            attacker_hit = False
        elif self.defenders.strength <= 0:
            attacker_hit = True
        else: 
            print ("attacker chance: " + str(chance(self.attackers.strength - self.defenders.strength)))
            attacker_hit = random.random() < chance(self.attackers.strength - self.defenders.strength)
#        attacker_hit, defender_hit = False, False
#        while attacker_hit == defender_hit:
#            attacker_hit = check_20_val(self.attackers.strength)
#            defender_hit = check_20_val(self.defenders.strength)
        
        self.attackers.update_exhaustion(attacker_hit)
        self.defenders.update_exhaustion(not attacker_hit)

        if attacker_hit:
            return self.attackers, self.defenders
        else:
            return self.defenders, self.attackers
    
    def curr_phase(self):
        global phases
        return phases[self.phase_index]
    
    def finish(self):
        print ("sending update for phase " + self.curr_phase() + " attacker index " + str(self.attackers.index) + 
               " defender index " + str(self.defenders.index) + " attacker strength " + str(self.attackers.get_strength(self.curr_phase())) +
               " defender strength " + str(self.defenders.get_strength(self.curr_phase())))
        event_manager.queue_event(Event(event_manager.COMBAT_UPDATE, [self.curr_phase(), self.attackers.index, self.defenders.index,
                                                                      self.attackers.get_strength(self.curr_phase()),
                                                                      self.defenders.get_strength(self.curr_phase())]))
        if self.is_dead():
            self.release_lock()
            
    
    def check_elimination(self, lose_force):
        win_group, lose_group = lose_force.opponent.group, lose_force.group
        winner_dead = win_group.check_elimination() # shouldn't ever be eliminated, but does certain neeeded upkeep
        assert(winner_dead == False)
        return lose_group.check_elimination()
    
    def handle_battle_end(self, lose_force, loser_eliminated):
        for force in self.forces:
            # clear temporary combat traits
            force.clear_temporary_traits()
            
        win_group, lose_group = lose_force.opponent.group, lose_force.group
        win_player, lose_player = win_group.get_owner(), lose_group.get_owner()

        self.victory_adjustments(win_group, lose_group, win_player, lose_player, loser_eliminated)
             
        retreat_chance = 0
        retreated = False
        if lose_force == self.defenders and not loser_eliminated and self.defense_hex.get_active_group() == lose_group:

            # check for retreat
            retreat_chance = self.retreat_chance(lose_group, win_group)
                    
            if random.random() < retreat_chance:
                # look for valid retreat hex
                retreat_dir = hexgrid.get_direction(win_group.get_hex(), lose_group.get_hex())        
                retreat_dirs = [(retreat_dir - 1) % 6, retreat_dir, (retreat_dir + 1) % 6]
                retreat_locs = [hexgrid.get_neighbor(lose_group.get_hex(), dir) for dir in retreat_dirs]

                retreat_hexes = [self.hex_map.get_hex(x, y) for x, y in retreat_locs]
                
                retreat_hexes = [curr_hex for curr_hex in retreat_hexes if (curr_hex != None and curr_hex.legal_move(lose_group)
                                                                                and not curr_hex.is_blocked(lose_group))]
                if len(retreat_hexes) > 0:
                    lose_group.move(random.choice(retreat_hexes), 0)
                    retreated = True
                    
            event_manager.queue_event(Event(event_manager.COMBAT_RETREAT, [win_group, lose_group, retreat_chance, retreated]))    
            
        # advance to retreat phase
        self.phase_index += 1
        return loser_eliminated
      
    def retreat_chance(self, lose_group, win_group):
             
        if lose_group.has_trait(trait.STUBBORN):
            retreat_chance = 0.0
        elif lose_group.all_has_trait(trait.ELUSIVE):
            retreat_chance = 1.0
        else:
            retreat_chance = BASE_RETREAT_CHANCE
            if win_group.army_fraction() > 0.0 and lose_group.army_fraction() == 0.0:
                retreat_chance += CHAR_V_ARMY_RETREAT_MODIFIER
            if win_group.get_max_moves() > lose_group.get_max_moves():
                retreat_chance -= FASTER_RETREAT_MODIFIER 
            elif lose_group.get_max_moves() > win_group.get_max_moves():
                retreat_chance += FASTER_RETREAT_MODIFIER 

        return retreat_chance
    
    def next_step(self):
        
        if self.curr_phase() == RETREAT:
                                                                             
            if self.defense_hex.get_defenders() == None:
                #  destroyed or drove out enemy, return to move process and keep moving
                self.paused_movement.unpause()
            else:
                # failure to drive out enemy, incomplete attack consumes some of attackers movement.
                self.paused_movement.abort()
                self.attackers.group.consume_movement(combat_move_cost(self.defense_hex))
            
            event_manager.queue_event(Event(event_manager.COMBAT_END, []))    
            
            self.succeed()
            return self.finish()
        
        
        # march through the pre-melee special phases.  If the special phase is totaly done,
        # go immediately to the next one, otherwise return in order to handle the resulting event on
        # the next do_next() call
        while self.curr_phase() != MELEE_COMBAT:
            done = self.handle_special(phase_traits[self.curr_phase()], phase_funcs[self.curr_phase()])
            if done:
                self.phase_index += 1
            else:
                return  self.finish()
            if self.curr_phase() == MELEE_COMBAT:
                self.attackers.index = 0
                self.defenders.index = 0
                self.skip_unusable_units(self.defenders)
                self.skip_unusable_units(self.attackers)
                self.attackers.update_melee_strength()
                self.defenders.update_melee_strength()
                return  self.finish()
        
        # check for loserf
        for force in self.forces:
            if force.at_end():
                loser_eliminated = self.check_elimination(force)
                self.rounds_left -= 1
                if loser_eliminated or self.rounds_left == 0:
                    self.handle_battle_end(force, loser_eliminated)
                    return
                else:
                    self.init_round()
                    return

        # if no victor yet,curr attacker and curr defender duke it out until only one side hits, that
        # side wins this round and forces the other unit to step aside
        winner, loser = self.trial_of_strength()
        
        assert not(self.attackers.at_end())
        assert not(self.defenders.at_end())
        
        if winner == loser == None:
            # both sides incompetent, no effect
            self.attackers.next_unit()
            self.defenders.next_unit()
            self.skip_unusable_units(self.attackers)
            self.skip_unusable_units(self.defenders)
        else:
            
            # check defense to see if losing side takes a hit. If attacker has crushing blow, multiple targets affected.
            for i in range(winner.curr_unit().trait_value(trait.CRUSHING_BLOW) + 1):
                check_block(loser, loser.index + i)
           
            # infect loser, if applicable
            if winner.curr_unit().has_trait(trait.INFECT) and not loser.curr_unit().is_alive():
                winner.group.summon_unit(winner.curr_unit().trait_value(trait.INFECT))
                winner.index += 1 # don't use next unit, because unit not changing
            
            loser.next_unit()
            self.skip_unusable_units(loser)
        
        self.attackers.update_melee_strength()
        self.defenders.update_melee_strength()
        
        return self.finish()
   
    def on_update(self, delta_ms):
        if not self.get_lock():
            return
        super(CombatProcess, self).on_update(delta_ms)
       
   
    # try to grab 'lock' (not really thread-safe, assumes only one thread driving combats at a time).  
    # if can't do so, return false. 
    # This serializes combats on the process manager, so that only one can proceed at a time.  This allows combat interface
    # to work correctly (showing human users all visible combats) when AI is generating many moves at once.
    def get_lock(self):
        global combat_locked_by
        
        # TODO: could lock only human visibile combats if events from non-human visible proceses were suppressed.
        # performance boost.  
        if combat_locked_by == self:
            return True
        
        if combat_locked_by == None:
            combat_locked_by = self
            event_manager.queue_event(Event(event_manager.COMBAT_START, [self.attackers.group, self.defenders.group, self.defense_hex]))
            return True
        
        return False
    
    def release_lock(self):
        global combat_locked_by
        if combat_locked_by == self:
            combat_locked_by = None

MAP_ATTACK_START = 0
MAP_ATTACK_FIRE = 1
MAP_ATTACK_DONE = 2

class MapAttackProcess(StepProcess):
    
    def __init__(self, source_hex, target_group, human_visible, paused_movement = None):
        super(MapAttackProcess, self).__init__(combat_delay[options.curr_options.own_combat_speed], human_visible)
        self.source_hex = source_hex
        self.target_group = target_group
        self.phase = MAP_ATTACK_START
        self.paused_movement = paused_movement
        
    def next_step(self):
        
        if self.phase == MAP_ATTACK_START:
            event_manager.queue_event(Event(event_manager.MAP_ATTACK_FIRE, [self.source_hex, self.target_group.get_hex()]))
        
        elif self.phase == MAP_ATTACK_FIRE:    
            def get_target():
                return self.target_group.get_unit(random.randint(0, self.target_group.num_units() - 1))
        
            target = get_target()
            while (not target.is_alive()):
                target = get_target()
            
            # map attack a bolt from the blue, ignores special defensive abilities and goes straight to armor
            block = check_20_val(target.get_armor()) #check_block(self.target_group, target_index)
            self.target_eliminated = False
            if block:
                event_manager.queue_event(Event(event_manager.MAP_ATTACK_BLOCK, [self.source_hex, self.target_group.get_hex()]))
            else:
                target.wound()
                self.target_eliminated = self.target_group.check_elimination()
                event_manager.queue_event(Event(event_manager.MAP_ATTACK_HIT, [self.source_hex, self.target_group.get_hex()]))
              
        else:
            if self.paused_movement != None and self.target_eliminated:
                    # moving group is toast! cancel self (so combat doesn't follow this) and the move that caused the map attack
                self.abort()
                self.paused_movement.abort()
            else:
                self.succeed()

            event_manager.queue_event(Event(event_manager.MAP_ATTACK_DONE, [self.source_hex, self.target_group.get_hex()]))
        
        self.phase += 1                                        
        
        