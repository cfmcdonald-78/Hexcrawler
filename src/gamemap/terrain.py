'''
Created on Jun 29, 2012

@author: Chris
'''
import mob.trait as trait, mob.move_mode as move_mode

class HexType(object):
    
    def __init__(self, name, move_cost, required_trait, settled = False, regrowth_chance = 0.0):
        self.name = name
        self.settled = settled
        self.move_cost = move_cost
        self.required_trait = required_trait
        self.regrowth_chance = regrowth_chance
    
    def is_settled(self):
        return self.settled
    def is_water(self):
        return self.required_trait == trait.NAVAL
    def is_forest(self):
        return self.name == "Forest" or self.name == "Grim Forest"

BASE_MOVE_COST = 2

PLAIN = HexType("Plain", 3, None)
SETTLED_PLAIN = HexType("Settled Plain", BASE_MOVE_COST, None, settled=True)
FOREST = HexType("Forest", 4, None, regrowth_chance=0.02)
HILL = HexType("Hill", 5, None)
SETTLED_HILL = HexType("Settled Hill", 3, None, settled=True)
MOUNTAIN = HexType("Mountain", 6, trait.MOUNTAINEER)
OCEAN = HexType("Ocean", BASE_MOVE_COST, trait.NAVAL)
DESERT = HexType("Desert", 3, trait.SUPPLY)
DESERT_HILL = HexType("Desert Hill", 5, trait.SUPPLY) 
VOLCANO = HexType("Volcano", 6, trait.MOUNTAINEER)
GRIM_FOREST = HexType("Grim Forest", 4, None)
SCORCHED = HexType("Scorched", 3, None)

def is_legal_terrain(hex_type, move_group):
    # if group is all flying, can cross any terrain
    if move_group.get_move_mode() == move_mode.FLIGHT:
        return True
    
    if move_group.has_trait(trait.AQUATIC):
        return hex_type.is_water()
    
    if move_group.has_trait(trait.SYLVAN) and hex_type.is_settled():
        return False
    
    # otherwise check for required trait
    req_trait = hex_type.required_trait
    return req_trait == None or (move_group.has_trait(req_trait) and move_group.get_highest_trait(req_trait) > 0)
    
    
settle_map = {"Forest": "Settled Plain", "Plain":"Settled Plain", "Hill": "Settled Hill"}
pillage_map = {"Settled Plain": "Plain", "Settled Hill": "Hill"}
hex_types = [PLAIN, SETTLED_PLAIN, FOREST, HILL, SETTLED_HILL, MOUNTAIN, OCEAN, DESERT, DESERT_HILL, VOLCANO, GRIM_FOREST, SCORCHED]
name_to_type = {"Plain": PLAIN, "Forest": FOREST, "Hill" : HILL, 
                "Mountain": MOUNTAIN, "Ocean":OCEAN, "Desert":DESERT, "Desert Hill": DESERT_HILL, 
                "Volcano":VOLCANO, "Grim Forest": GRIM_FOREST, "Settled Plain": SETTLED_PLAIN, "Settled Hill": SETTLED_HILL} 
terrain_nouns = {
    PLAIN: ["Grassland", "Prarie", "Plain", "Plains", "Expanse", "Lowland", "Lowlands", "Plateau", "Steppe", "Veldt", "Meadow"],
    FOREST: ["Forest", "Timber", "Wood", "Woods", "Woodland", "Jungle", "Grove", "Thicket", "Bramble"],
    HILL: ["Hills", "Downs", "Foothills", "Bluffs", "Moor", "Moors", "Knolls", "Highland", "Highlands", "Uplands"], 
    MOUNTAIN: ["Cliffs", "Crags", "Palisades", "Range", "Mountains", "Peaks", "Slopes", "Summits", "Cuillins", "Massif"], 
    OCEAN: ["Ocean", "Sea", "Deep", "Deeps", "Main",  "Waters", "Tide"], 
    DESERT: ["Desert", "Deserts", "Desolation", "Sere", "Sand", "Sands", "Dunes"], 
    DESERT_HILL: ["Desert", "Deserts", "Desolation", "Sere", "Sand", "Sands", "Dunes"], 
    VOLCANO:  ["Cliffs", "Crags", "Palisades", "Range", "Mountains", "Peaks", "Slopes", "Summits", "Cuillins", "Massif"], 
    GRIM_FOREST: ["Forest", "Wood", "Woods", "Woodland", "Grove", "Thicket", "Weald", "Bramble"]
}

