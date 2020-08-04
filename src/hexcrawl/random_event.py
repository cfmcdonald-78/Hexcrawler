'''
Created on Jul 23, 2012

@author: Chris
'''
import core.event_manager as event_manager
from core.event_manager import Event
from mob.group import Horde, horde_types_by_name
from gamemap.site import Site
import mob.unit as unit, mob.trait as trait, mob.hero as hero, mob.group as group
import gamemap.site_type as site_type, gamemap.hexgrid as hexgrid
import fame
import random
from math import ceil
from util.tools import min_in_list

WEEKS_PER_HORDE_LEVEL = 4
HORDE_CHANCE_PER_DAY = 0.08
horde_chance = HORDE_CHANCE_PER_DAY

FIRE_SPREAD_CHANCE = 0.1
MIN_FIRE_DURATION = 2
MAX_FIRE_DURATION = 4

MIN_HERO_LAIR_LEVEL = 2
MAX_HERO_LAIR_LEVEL = 6

HORDE = "Horde"

def generate_horde(game, curr_week):
    global horde_chance
    
    # cumulative chance for horde, chance increases each time horde fails to appear, resets to 0
    # if horde does appear
    if random.random() > horde_chance:
        horde_chance += HORDE_CHANCE_PER_DAY
        return None, None
    
    horde_chance = 0
    
    # over time, hordes get nastier!
    horde_level = (curr_week / WEEKS_PER_HORDE_LEVEL) + 1
    candidate_horde_types = [horde_type for horde_type in horde_types_by_name.values() if horde_type.level == horde_level]
    assert(len(candidate_horde_types) > 0)
    
    # find site types where hordes of given level can appear
    site_type_names = set([])
    for candidate in candidate_horde_types:
        site_type_names.update(set(candidate.site_names))
            
    # find all such sites on the map
    candidate_sites = []
    for site_type_name in site_type_names:
        candidate_sites += game.get_map().find_site(site_type_name, find_all = True)
        
    if len(candidate_sites) > 0:
        # if there's at least one active site of the right type, generate a horde there.    
        horde_site = random.choice(candidate_sites)
        candidate_horde_types = [horde_type for horde_type in candidate_horde_types if horde_site.get_type().name in horde_type.site_names]
        horde_type = random.choice(candidate_horde_types)
    
        # find the goal of the horde: nearest city-state on the map to its site
        site_hex = horde_site.get_hex()
        city_states = game.get_map().find_site(horde_type.goal_type_name, find_all = True)
        goal_site, goal_dist = min_in_list(city_states, lambda city_state : hexgrid.get_distance(city_state.get_hex(), site_hex))
    
        spawn_hex = game.get_map().get_spawn_hex(site_hex)
        if spawn_hex == None:
            print "Alert: horde unable to generate due to all site hex neighbors being occupied"
            return None, None
    
        horde = Horde(horde_type, horde_site.get_owner(), goal_site.get_hex())
        horde.initialize(spawn_hex)
        return "A " + horde_type.name + " appears in ", game.get_map().get_zone(site_hex.x, site_hex.y)
    
    # no valid sites from which to spawn
    return None, None


# TODO: make storms/flooding more likely in wilder areas
def flooding(game):
    flood_zone = game.get_map().get_random_zone()
    
    days = random.randint(3, 9)
    found_river = False
    for hex_loc in flood_zone.hex_locs:
        curr_hex = game.get_map().get_hex(hex_loc.x, hex_loc.y)
        if curr_hex.has_river():
            curr_hex.river.flood(days)
            found_river = True
    
    
    if not found_river:
        # no rivers in chosen zone.  Returning no event instead of trying new zone makes floods less
        # likely the fewer rivers there are on the map
        return None, None
    
    return "Flooding has made the rivers impassable in ", flood_zone

storm_severity_strings = {1:"Storms", 2: "Heavy storms", 3: "Raging storms"}

def storms(game):
    storm_zone = game.get_map().get_random_zone()
    days = random.randint(1, 3)  # really 1-3, since day start will immediately decrement 1 day
    severity = random.randint(1, 3)
    for hex_loc in storm_zone.hex_locs:
        curr_hex = game.get_map().get_hex(hex_loc.x, hex_loc.y)
        curr_hex.set_storm(days, severity)

    return storm_severity_strings[severity] + " are making travel difficult across ", storm_zone

# a cache of treasure is placed in the wild. 
#def hidden_treasure(game):
#    placed_location = game.get_map().place_site(site_type.site_types["Cache"], 
#                                                random.randint(3, 4), game.npc_table,
#                                                required_zone_types=['Wild', 'Nautical'])
#    if placed_location == None:
#        return None, None
#    else:
#        return "There are rumors of hidden treasure in ", game.get_map().get_zone(placed_location.x, placed_location.y)
# 
# a hero is placed as the prisoner in a lair.  Each time this event happens, the level of the lair goes up, until it can go no higher
#def hero_in_chains(game):
#    next_lair_level = game.get_event_data().get_next_hero_lair_level()
#    if  next_lair_level == None:
#        return None, None
#    
#    lair_candidates = game.get_map().find_site("Lair", level_range = (next_lair_level, next_lair_level), find_all = True)
#    if len(lair_candidates) == 0:
#        return None, None
#
#    chosen_lair = random.choice(lair_candidates)
#    chosen_lair.set_prisoner(hero.Hero())
#    game.get_event_data().update_hero_lair_level()
#     
#    return "There are rumors of a hero imprisoned in ", game.get_map().get_zone(chosen_lair.get_hex().x, chosen_lair.get_hex().y)

def questing_beast(game):
    monster_type = unit.random_type_with_trait(trait.QUEST)
    
    start_hex = game.get_map().get_random_hex(lambda curr_hex : curr_hex.hex_type.is_forest() and not curr_hex.has_occupants())
    
    if start_hex == None:
        # no available hex!
        return None, None
    
    beast = unit.Unit(monster_type)
    beast.set_trait(trait.SUMMONED, random.randint(5, 10))
    monster_group = group.QuestingBeast(game.npc_table["Chaos"]) 
    monster_group.add_unit(beast)
    monster_group.set_reputation_value(beast.get_level())
    monster_group.initialize(start_hex)
    
    return "A questing beast has been sighted in ", game.get_map().get_zone(start_hex.x, start_hex.y)

def sea_monster(game):
    monster_type = unit.random_type_with_trait(trait.AQUATIC)
    
    start_hex = game.get_map().get_random_hex(lambda curr_hex : curr_hex.hex_type.is_water() and not curr_hex.has_occupants())
    
    if start_hex == None:
        # no water on this map!
        return None, None
    
    sea_monster = unit.Unit(monster_type)
    sea_monster.set_trait(trait.SUMMONED, random.randint(4, 8))
    monster_group = group.Wanderer(game.npc_table["Chaos"]) 
    monster_group.add_unit(sea_monster)
    monster_group.set_reputation_value(sea_monster.get_level())
    monster_group.initialize(start_hex)
    
    return "A sea monster has been sighted near ", game.get_map().get_zone(start_hex.x, start_hex.y)

def forest_fire(game):
    def is_valid_fire_hex(curr_hex):
        if curr_hex.get_active_group() != None:
            return False
        
        if curr_hex.has_site():
            return False
        
        if not curr_hex.hex_type.is_forest():
            return False
        
        return True
    
    fire_hex = game.get_map().get_random_hex(is_valid_fire_hex)
    if fire_hex == None:
        return None, None
    
    fire_hex.set_fire(random.randint(MIN_FIRE_DURATION, MAX_FIRE_DURATION))
    return "A forest fire has erupted in ", game.get_map().get_zone(fire_hex.x, fire_hex.y)

def agent_of_chaos(game):
    def is_valid_agent_hex(curr_hex):
        if curr_hex.active_group != None:
            return False
        
        if curr_hex.has_site():
            return False
        
        if curr_hex.hex_type.name != "Settled Plain":
            return False
        
        map_data = game.get_map()
        if map_data.get_zone(curr_hex.x, curr_hex.y).zone_type.name != "Civilized":
            return False 
        
        return True
    
    agent_hex = game.get_map().get_random_hex(is_valid_agent_hex)
    if agent_hex == None:
        print "couldn't find hex for agent of chaos!"
        return None, None
    
    target_player = random.choice([curr_player for curr_player in game.get_players() if curr_player.is_actor()])
    target_unit = random.choice(target_player.get_heroes())
    
    agent = unit.Unit(unit.unit_types_by_name["Agent of Chaos"])
    agent.set_trait(trait.SUMMONED, random.randint(10, 20))  
    monster_group = group.Assassin(game.npc_table["Chaos"], target_unit) 
    monster_group.add_unit(agent)
    monster_group.initialize(agent_hex)
    
    return "An agent of chaos is on the loose in ",  game.get_map().get_zone(agent_hex.x, agent_hex.y)

#def dwarven_expedition(game):
#    placed_location = game.get_map().place_site(site_type.site_types["Fortress"], 
#                                                5, game.npc_table,
#                                                required_zone_types=['Wild'])
#    if placed_location == None:
#        return None, None
#    else:
#        return "A dwarven expedition has set up camp in ", game.get_map().get_zone(placed_location.x, placed_location.y)
#
#def elven_delegation(game):
#    placed_location = game.get_map().place_site(site_type.site_types["Glade"], 
#                                                5, game.npc_table,
#                                                required_zone_types=['Wild'])
#    if placed_location == None:
#        return None, None
#    else:
#        return "An elven delegation has set up camp in ", game.get_map().get_zone(placed_location.x, placed_location.y)
#


def grant_hero(game):
    grantee = random.choice([player for player in game.get_players() if player.is_actor()])
    
    # can only get hero if above certain fame threshold, higher the more heroes you've been granted so far
    if (grantee.num_heroes_granted() >= len(fame.HERO_GRANT_THRESHOLD) or 
        grantee.get_fame() < fame.HERO_GRANT_THRESHOLD[grantee.num_heroes_granted()]):
        return None, None
    
    hero_sites = [curr_site for curr_site in grantee.get_sites() if curr_site.is_haven()]
    if len(hero_sites) == 0:
        # nowhere for hero to appear
        return None, None
    
    grant_site = random.choice(hero_sites)
    
    # generate hero
    hero_type = unit.random_hero_type()
    
    granted_hero = hero.Hero(hero_type)
    grant_site.add_for_hire(granted_hero)
    grantee.granted_hero()
    
    # signal the granting of a hero
    event_manager.queue_event(Event(event_manager.HERO_GRANTED, 
                                    [grantee, grant_site.get_name()]))
    return "A new hero has appeared in ", game.get_map().get_zone(grant_site.get_hex().x, grant_site.get_hex().y)

 
def abyssal_gate(game):
    placed_location = game.get_map().place_site(site_type.site_types["Gate"], 
                                                7, game.npc_table,
                                                required_zone_types=['Deep Wild', 'Wild'])
    if placed_location == None:
        return None, None
    else:
        return "A gate to the abyss has erupted in ", game.get_map().get_zone(placed_location.x, placed_location.y)


# event tables: (event_function, first week event can occur)
common_events = [(grant_hero, 0) , (storms, 0),  (flooding, 0),  (abyssal_gate, 29)]
uncommon_events = [ (forest_fire, 0), (agent_of_chaos, 5),  (sea_monster, 3) ]
rare_events = [(questing_beast, 0) ]  # need more rare events!!   

EVENT_CHANCE =  0.5
UNCOMMON_THRESHOLD = 0.7
RARE_THRESHOLD = 0.95

def choose_event_func(event_list, curr_week):
    return random.choice([event_func for event_func, earliest_week in event_list if earliest_week <= curr_week])

def check_for_event(game):
    curr_week = game.get_turn().week
    # first check to see if a horde is spawned. 
    event_description, event_zone = generate_horde(game, curr_week) 
    
    # if no horde, check for normal random event
    if event_description == None:
        # TODO: scale chance of event with map size to get constant chance/area
        if random.random() > EVENT_CHANCE:
            return
        
        # determine type of event
        event_type_roll = random.random()
        if event_type_roll > RARE_THRESHOLD:
            event_func = choose_event_func(rare_events, curr_week)
        elif event_type_roll > UNCOMMON_THRESHOLD:
            event_func = choose_event_func(uncommon_events, curr_week)
        else:
            event_func = choose_event_func(common_events, curr_week)
        event_description, event_zone = event_func(game)
    
    if event_description == None:
        return   
    
    event_manager.queue_event(Event(event_manager.RANDOM_EVENT, [event_description + event_zone.get_name()]))
    
def seed_map(hex_map):
    # place heroes as prisoners in lairs, 1 for each level of lair
    for i in range(MIN_HERO_LAIR_LEVEL, MAX_HERO_LAIR_LEVEL + 1):
        lair_candidates = hex_map.find_site("Lair", level_range = (i, i), find_all = True)
        if len(lair_candidates) == 0:
            continue
        
        chosen_lair = random.choice(lair_candidates)
        chosen_lair.set_prisoner(hero.Hero(unit.random_hero_type()))
    