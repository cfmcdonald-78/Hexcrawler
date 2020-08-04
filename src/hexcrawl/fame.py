'''
Created on Jan 2, 2013

@author: Chris
'''
'''
Created on Jul 10, 2012

@author: Chris
'''

# a player can only gain reputation by beating a group/site if his REP_GAIN_THRESHOLD[level - 1] is less than 
# the player's current fame.  If not, this group/site is beneath him, and not worth additional rep
REP_GAIN_THRESHOLD = [20, 60, 120, 200, 300, 420, 560]
HORDE_THRESHOLD = [20, 60, 120, 200, 300, 420, 560]

HERO_GRANT_THRESHOLD = [30, 120, 300, 600, 1000]


DESTROYED_GROUP = 0
LOOTED_SITE = 1
BUILT_SITE = 2

LOOT_FAME = "Looted Sites"
KILL_FAME = "Defeated Groups"
BUILD_FAME = "Built Sites"

fame_events = [DESTROYED_GROUP, LOOTED_SITE, BUILT_SITE]
fame_type_map = {LOOTED_SITE:LOOT_FAME,  DESTROYED_GROUP:KILL_FAME, BUILT_SITE: BUILD_FAME}

FAME_TYPES = [LOOT_FAME, KILL_FAME, BUILD_FAME]

def adjust_fame(event_type, target, acting_player):
    if not acting_player.is_actor():
        return 0
    
    delta = target.get_level()
    acting_player.adjust_fame(delta, fame_type_map[event_type])
     
    return delta    
