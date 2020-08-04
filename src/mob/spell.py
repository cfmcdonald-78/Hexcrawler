'''
Created on Apr 29, 2013

@author: Chris
'''
import trait

WHITE = "White"
RED = "Red"
GREEN = "Green"
BLACK = "Black"

mana_types = [WHITE, GREEN, RED, BLACK]

def white_source(hexes):
    #civilized site
    for curr_hex in hexes:
        if curr_hex.has_site() and curr_hex.site.settles():
            return True
    return False

def green_source(hexes):
    # forest
    for curr_hex in hexes:
        if curr_hex.hex_type.name == "Forest":
            return True
    return False

def red_source(hexes):
    for curr_hex in hexes:
        if curr_hex.hex_type.name == "Volcano":
            return True
    return False

def black_source(hexes):
    for curr_hex in hexes:
        if curr_hex.active_group and curr_hex.active_group.get_owner().name == "Chaos":
            return True
        if curr_hex.garrison and curr_hex.garrison.get_owner().name == "Chaos":
            return True
    return False


mana_source_func = {WHITE: white_source, GREEN: green_source, RED: red_source, BLACK: black_source}
mana_trait = {WHITE: trait.WHITE_MANA, GREEN: trait.GREEN_MANA, RED: trait.RED_MANA, BLACK: trait.BLACK_MANA}

# returns true if mana of given type available,
# given 7 hex region
def mana_available(mana_type, center_hex, neighbors):
    # look for unit source in center hex
    if center_hex.active_group and center_hex.active_group.has_trait(mana_trait[mana_type]):
        return True
    if center_hex.garrison and center_hex.garrison.has_trait(mana_trait[mana_type]):
        return True
    
    # look for particular source
    return mana_source_func[mana_type]([center_hex] + neighbors)


class Spell(object):
    
    def __init__(self, name, mana_type, proc):
        self.name = name
        self.mana_type = mana_type
        self.proc = proc

    def castable(self, caster_hex, hex_map):
        return mana_available(self.mana_type, caster_hex, hex_map.get_neighbors(caster_hex))
        
    def cast(self, caster_hex, hex_map):
        if not self.castable(caster_hex, hex_map):
            assert(False)
        
        self.proc(caster_hex, hex_map)
        
class Scroll(object):
    
    def __init__(self, spell):
        self.spell = spell

#     s
#•    All duration spells last for a week

# scrolls consumed when used.  Cost 50 gold at Mage Tower site
#
# Mage Tower: global alloc 0.15 per zone. 
# 
#•    Some way to allow for either dabbling or specializing as caster (at cost to regular combat ability)
#
#
#•    Soothe Nature (Green): immediately end all flooding and/or storms in zone
#     Gentle Rain (Green): immediately end all fires in zone and heal random unit in group 
#•    Summon Beast (Green): summon beast (duh) [duration]
#•    Summon Lightning (Green): ranged 10 against random adjacent enemy unit
#•    Veil of the Forest (Green): become hidden [duration]
#•    Heroes’ Feast(White): create supply wagon 
#•    Inspire the People (White): nearest friendly site that settles immediately attempts to expand its settled range 
#•    Heavenly Rampart (White): +2  armor to all units in group [duration]
#•    Heavenly Spears (White): +1  strength to all units in group [duration]
#•    Black March (Black): Wound all units in group to triple normal move rate
#•    Vile Sputum (Black): ranged 8, Pierce 3 against random adjacent enemy unit
#     Hateful Gaze (Black): 
#     Aura of Death (Black): gain Death aura 7, vampiric [duration]
#     Dark Ritual (Black): Kill random unit in group (other than hero) to grant all others +1 attack/armor [duration]
#•    Blood of Flame (Red): Strength +4, armor -4 [duration]
#•    Hand of Flame (Red):  gain Ranged 10, Splash, and Army Attack [duration]
#     Heart of Flame (Red): 
#     Eye of Flame (Red): 
        
    