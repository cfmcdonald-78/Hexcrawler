'''
Created on Sep 1, 2012

@author: Chris
'''

PER_LEVEL_COST = 'per_level'
FLAT_COST = 'flat'

ARMOR = "Armor"
SPOT = "Spot"
IMPEDE = "Impede"
INCOME_BONUS = "Income bonus"
MAP_ATTACK = "Map attack"
SIGHT = "Sight"
RECRUIT = "Recruit"
SETTLE = "Settle"
REVOLT_STRENGTH = "Revolt strength"
ITEM = "Item storage"


class SiteUpgrade(object):
    def __init__(self, name, valid_site_types, min_level, cost, prereqs, effects, description):
        self.name = name
        self.valid_site_types = valid_site_types
        self.min_level = min_level
        self.cost = cost
        self.prereqs = prereqs
        self.effects = effects
        self.description = description

    def get_cost(self, site):
        if self.cost['type'] == PER_LEVEL_COST:
            return self.cost['amount'] * site.get_level()
        return self.cost['amount']

upgrades = []
upgrades_by_name = {}

def available_upgrades(site):
    candidates = filter(lambda upgrade : site.get_type().name in upgrade.valid_site_types and site.get_level() >= upgrade.min_level,
                        upgrades) 
    
    # site can't have same upgrade twice
    curr_upgrades = site.get_upgrades()
    candidates = filter(lambda upgrade : upgrade.name not in curr_upgrades,
                        candidates)
    
    # site can't have upgrade with pre-req that it hasn't met
    candidates = filter(lambda upgrade: upgrade.prereqs == None or all([prereq in curr_upgrades for prereq in upgrade.prereqs]),
                        candidates)
    
    return candidates