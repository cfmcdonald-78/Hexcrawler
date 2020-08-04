'''
Created on Jul 13, 2012

@author: Chris

Event handling system
'''
from util.tools import BIGNUM
from util.linked_list import LinkedQueue
from collections import namedtuple, deque

UNLIMITED = BIGNUM

class EventType(object):
    
    def __init__(self, name, data_labels):
        self.name = name
        self.data_labels = data_labels

#COMMAND EVENTS
COMMAND_ISSUED = EventType("CommandIssued", ['command'])

# COMBAT EVENTS
COMBAT_START = EventType("CombatStart", ['attackers', 'defenders', 'hex_loc'])
COMBAT_END = EventType("CombatEnd", [])
COMBAT_UPDATE = EventType("CombatUpdate", ['phase', 'attacker_index', 'defender_index', 'attacker_strength', 'defender_strength'])
UNIT_BLOCK = EventType("UnitBlock", ['group', 'index'])
UNIT_HIT = EventType("UnitHit", ['group', 'index'])
UNIT_HEAL = EventType("UnitHeal", ['group', 'index'])
RANGED_ATTACK = EventType("RangedAttack", ['group', 'index'])
#TRIAL_OF_STRENGTH = EventType("TrialOfStrength", ['attacker_strength', 'defender_strength'])
HEAL_ATTEMPT = EventType("HealAttempt", ['group', 'index'])
COMBAT_RETREAT = EventType("CombatRetreat", ['win_group', 'lose_group', 'retreat_chance', 'retreated'])
COMBAT_SPOILS = EventType("CombatSpoils", ['reputation', 'item'])

# MAP ATTACK EVENTS
MAP_ATTACK_FIRE = EventType("MapAttackFire", ['origin_loc', 'target_loc'])
MAP_ATTACK_HIT = EventType("MapAttackHit", ['origin_loc', 'target_loc'])
MAP_ATTACK_BLOCK = EventType("MapAttackBlock", ['origin_loc', 'target_loc'])
MAP_ATTACK_DONE = EventType("MapAttackDone", ['origin_loc', 'target_loc'])

# SITE_EVENTS
LOOTING = EventType("Looting", ['looting_player', 'hex_loc', 'site_name', 'gold', 'reputation', 'item_text', 'prisoner_text'])
#LOOT_START = EventType("LootStart", ['hex_loc', 'site_name'])
#LOOT_GOLD = EventType("LootGold", ['amount'])
#LOOT_PRISONER = EventType("LootPrisoner", ['name'])
#LOOT_ITEM = EventType("LootItem", ['name'])
#LOOT_REPUTATION = EventType("LootReputation", ['amount'])
#LOOT_END = EventType("LootEnd", [])
SITE_LOOTED = EventType("SiteLooted", ['player', 'site'])
SITE_UPGRADED = EventType("SiteUpgraded", ['site', 'upgrade'])
SITE_REVOLT = EventType("SiteRevolt", ['site', 'former_owner'])

# MOVE EVENTS
MOVE_DONE = EventType("MoveDone", ['group', 'hex_start', 'hex_loc'])

# TURN EVENTS
DAY_START = EventType("DayStart", ['week', 'day'])
WEEK_START = EventType("WeekStart", ['week'])
TURN_START = EventType("TurnStart", ['player', 'week', 'day'])
TURN_END= EventType("TurnEnd", ['player', 'week', 'day'])
RANDOM_EVENT= EventType("RandomEvent", ['description'])

# UNIT EVENTS
UNIT_DEATH = EventType("UnitDeath", ['group', 'index'])
UNIT_REMOVED = EventType("UnitRemoved", ['group'])
UNIT_ADDED = EventType("UnitAdded", ['group'])
UNIT_SHIFTED = EventType("UnitShifted", ['group', 'old_index', 'new_index'])
HERO_GAINED = EventType("HeroGained", ['player'])
HERO_LOST = EventType("HeroLost", ['player'])
UNIT_STATS_CHANGED = EventType("UnitStatsChanged", ['unit'])
UNIT_TRAIT_USED = EventType("UnitTraitUsed", ['unit', 'trait'])

# ITEM EVENTS
ITEM_REMOVED = EventType("ItemRemoved", ['unit'])
ITEM_ADDED = EventType("ItemAdded", ['unit'])
ITEM_SHIFTED = EventType("ItemShifted", ['unit'])

# PLAYER EVENTS
PLAYER_LOST = EventType("PlayerLost", ['player', 'description'])
HERO_GRANTED = EventType("HeroGranted", ['player', 'site_name'])
PLAYER_WON = EventType("PlayerWon", ['player', 'description'])
SITE_LOST = EventType("SiteLost", ['player', 'site_name'])
PLAYER_STATUS_CHANGE = EventType("PlayerStatusChange", ['player', 'status', 'new_value'])
#GAME_OVER = EventType("GameOver", ['winner'])

# UI EVENTS
MODAL_DIALOG = EventType("ModalDialog", ['dialog', 'new_state'])
HEX_SELECTED = EventType("HexSelected", ['loc'])
UNIT_SELECTED = EventType("UnitSelected", ['unit'])
BUTTON_CLICK = EventType("ButtonPush", ['button', 'state'])
SOUND_CHANGE = EventType("SoundChange", ['on'])
MUSIC_CHANGE = EventType("MusicChange", ['on'])
COMBAT_SPEED_CHANGE = EventType("CombatSpeedChange", ['self', 'speed'])
QUIT        =  EventType("Quit", ['save'])
TICK        = EventType("Tick", [])

class Event(object):
    
    def __init__(self, type, data):
        self.type = type
        self.data = {}
        for i in range(len(data)):
            self.data[type.data_labels[i]] = data[i]

    def get_type(self):
        return self.type
    
    def get_data(self):
        return self.data

#UnitDeath
#TurnStart
#UnitWound
#UnitHeal
#GroupMove
#GroupSelect

event_listeners = {}
event_queues = [deque(), deque()]  # one queue takes incoming events while other queue being processed
active_queue_index = 0

def inactive_queue():
    global active_queue_index, event_queues
    return event_queues[(active_queue_index + 1) % len(event_queues)]

def active_queue():
    global active_queue_index, event_queues
    return event_queues[active_queue_index]

def swap_queues():
    global active_queue_index
    active_queue_index = (active_queue_index + 1) % len(event_queues)


def add_listener_multi(callback, event_types):
    for event_type in event_types:
        add_listener(callback, event_type)

def add_listener(callback, event_type):
    global event_listeners
    if event_type in event_listeners:
        curr_listeners = event_listeners[event_type]
        for listener in curr_listeners:
            if listener == callback:
                raise ValueError("attempted to double register callback " + str(callback) + " for " + str(event_type))
        curr_listeners.append(callback)
    else:
        event_listeners[event_type] = [callback]

def remove_listener_multi(callback, event_types):
    for event_type in event_types:
        remove_listener(callback, event_type)
        
def remove_listener(callback, event_type):
    global event_listeners
    if event_type in event_listeners:
        curr_listeners = event_listeners[event_type]
        curr_listeners.remove(callback)
    else:
        raise ValueError("attempted to double remove callback " + str(callback) + " from " + str(event_type) + " for which it wasnt registered")

# cause event to happen immediately without queuing for update
def trigger_event(event):
    global event_listeners
    
    callbacks = event_listeners.get(event.get_type(), [])
    for callback in callbacks:
        callback(event)

def queue_event(event):
#    print "received event: " + event.type.name
    global event_listeners
    if event.get_type() in event_listeners:
        active_queue().appendleft(event)
        return True
    else:
        # don't queue events that no one cares about
        return False

# aborts the closest event to the front of the queue of the given type, or all of that type of all_of_type is true
def abort_event(event_type, all_of_type = False):
    pass

def abort_all_events():
    active_queue().clear()
    swap_queues()
    active_queue().clear()

def reset():
    global event_listeners
    abort_all_events()
    event_listeners = {}
    

# processes events until queue is empty or it runs out of time, if time_limit set
def tick_update(time_limit = UNLIMITED):
    process_queue = active_queue()
    swap_queues()
    active_queue().clear()
    
    while len(process_queue) > 0:
        curr_event = process_queue.pop()
#        print "processing event " + str(curr_event.type.name) + " " + str(curr_event.data)
        trigger_event(curr_event)
#        callbacks = event_listeners.get(curr_event.get_type(), [])
#        for callback in callbacks:
#            callback(curr_event)
        
         # TODO: add check to see if time up
         
    # TODO: add check to see if queue emptied.  If not, push events onto front of new active queue.



    


