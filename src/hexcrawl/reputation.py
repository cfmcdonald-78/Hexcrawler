'''
Created on Jul 10, 2012

@author: Chris
'''
import fame
import mob.trait as trait

LOOTED_SITE = fame.LOOTED_SITE
DESTROYED_GROUP = fame.DESTROYED_GROUP
BUILT_SITE = fame.BUILT_SITE
GAINED_UNIT = 3
LOST_UNIT = 4
LOST_BATTLE = 5
ITEM_EQUIP = 6
ITEM_UNEQUIP = 7

LOOT_REP = "Looted Sites"
UNIT_REP = "Units"
ITEM_REP = "Items"
KILL_REP = "Defeated Groups"
BUILD_REP = "Built Sites"

rep_type_map = {fame.LOOTED_SITE:LOOT_REP, GAINED_UNIT:UNIT_REP, LOST_UNIT: UNIT_REP, 
           fame.DESTROYED_GROUP:KILL_REP, ITEM_EQUIP:ITEM_REP, ITEM_UNEQUIP:ITEM_REP,
           fame.BUILT_SITE: BUILD_REP}

REPUTATION_TYPES = [LOOT_REP, UNIT_REP, ITEM_REP, KILL_REP, BUILD_REP]

def adjust_reputation(event_type, target, acting_player, delta=0):
    if not acting_player.is_actor():
        return 0
    
    if event_type in fame.fame_events:
        fame.adjust_fame(event_type, target, acting_player)
    
    target_level = target.get_level()
    
    if event_type == DESTROYED_GROUP:
        delta = target.get_reputation_value()
    
    if event_type == LOST_BATTLE:
        # penalty to high rep players for losing battles to weak foes
        if acting_player.get_reputation() >= fame.REP_GAIN_THRESHOLD[target_level - 1]:
            delta = -1
            
    if event_type == LOOTED_SITE:
        delta = target.site_type.loot_effects.reputation * target_level
        
    if event_type == BUILT_SITE:
        delta = -target.site_type.loot_effects.reputation * target_level
    
    if event_type == GAINED_UNIT:
        delta = target.trait_value(trait.REPUTATION) 
    
    if (delta > 0 and acting_player.get_fame() >= fame.REP_GAIN_THRESHOLD[target_level - 1]):
        delta = 0
    
    # make sure we exactly reverse reputation change made when gaining unit/item
    # regardless of current fame threshold
    if event_type == LOST_UNIT or event_type == ITEM_UNEQUIP:
        delta = -target.reputation_change
    
    if event_type == GAINED_UNIT or event_type == ITEM_EQUIP:
        target.reputation_change = delta
    
    acting_player.adjust_reputation(delta, rep_type_map[event_type])
     
    return delta    
    
# neutral sites will bar you from entry if your reputation is too low, if it's still
# lower, patrols from the site will actively attack you.
#def neutral_site_hostile(site_level, player_reputation):
#    return player_reputation < SITE_OPEN_THRESHOLD[site_level - 1]
#
#def neutral_patrol_hostile(patrol_level, player_reputation):
#    return player_reputation < NEUTRAL_HOSTILITY_THRESHOLD[patrol_level - 1]