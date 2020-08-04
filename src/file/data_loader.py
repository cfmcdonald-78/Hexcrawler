'''
Created on Jul 3, 2012

@author: Chris
'''
import json, os, random
import mob.unit as unit, hexcrawl.loot as loot, mob.item as item, mob.group as group
import gamemap.site_type as site_type, gamemap.site_upgrade as site_upgrade, gamemap.zone_type as zone_type 
import hexcrawl.player_type as player_type
import collections


def load_name_maker(json_name_maker):
    return json_name_maker

def gen_prisoner_candidates(unit_types, site_types, prisoner_candidates):
    men_site_types = [curr_site_type for curr_site_type in site_types.values() if curr_site_type.owner_name == "Men"]
    for unit_type in unit_types:
        for men_site_type in men_site_types:
            if men_site_type.name in unit_type.sites:
                prisoner_candidates.append(unit_type)
                break
    return prisoner_candidates

def load_player_type(json_player):
    name = json_player["name"]
    base_type = json_player["base_type"]
    color = json_player["color"]
    patrol_ai = json_player["patrol_ai"]
    patrol_reputation = json_player["patrol_reputation"]
    hostility_func = json_player["actor_hostility_func"]
    hostility_table = json_player["actor_hostility_table"]
    hostile_to = json_player["hostile_to"]
    
    return player_type.NPCPlayerType(name, base_type, color, patrol_reputation, patrol_ai, hostile_to, hostility_func, hostility_table)

def load_base_items(json_item_type):
    name = json_item_type['name']
    item_type = json_item_type['type']
    subtype = json_item_type.get('subtype', None)
    quality = json_item_type['quality']
    level = json_item_type['level']
    traits = json_item_type['traits']
    return item.BaseItem(name, item_type, subtype, quality, level, traits)

def load_item_mods(json_item_type):
    adjective = json_item_type['adjective']
    types = json_item_type['types']
    level = json_item_type['level']
    traits = json_item_type['traits']
    return item.ItemModifier(adjective, types, level, traits)

def load_horde_type(json_horde_type):
    name  = json_horde_type['name']
    leader = json_horde_type['leader']
    level = json_horde_type['level']
    units = json_horde_type['units']
    sites = json_horde_type['sites']
    goal = json_horde_type['goal']
    
    return group.HordeType(name, leader, level, units, sites, goal)

def load_unit_type(json_unit_type):
    name = json_unit_type["name"]
    is_army = json_unit_type["is_army"]
    # assume is combatant if combatant property not present
    is_combatant = ("combatant" not in json_unit_type)  or json_unit_type["combatant"]
    level = json_unit_type["level"]
    strength = json_unit_type["strength"]
    armor = json_unit_type["armor"]
    move = json_unit_type["move"]
    looting = json_unit_type["looting"]
    traits = json_unit_type["traits"]
    sites = json_unit_type["sites"]
    
    if name in DataLoader.name_makers:
        name_maker = DataLoader.name_makers[name]
    else:
        name_maker = None
    
    return unit.UnitType(name, name_maker, is_army, is_combatant, level, strength, armor, move, looting, traits, sites)

def load_zone_type(json_zone_type):
    name = json_zone_type["name"]
    type = json_zone_type["type"]
        
    site_infos = json_zone_type["sites"]
    site_param_list = []
    for site_info in site_infos:
        param_site_type = site_type.site_types[site_info["name"]]
        site_params = zone_type.SiteParams(param_site_type, site_info["frequency"], site_info["min_level"], site_info["max_level"])
        site_param_list.append(site_params)
    
    weights = None
    substitution = None
    if type == "base":
        weights = json_zone_type["weights"]
    else:
        sub_info = json_zone_type["substitution"]
        substitution = zone_type.Substitution(sub_info["sub_for"],sub_info["frequency"],sub_info["function"], sub_info["params"],
                                              sub_info["terrain"])
        #TerrainSub = collections.namedtuple('TerrainSub', ['new_terrain', 'function', 'params'])
    min_fraction = json_zone_type["min_fraction"]
    
    zone_type.type_adjectives[name] = json_zone_type["adjectives"]
        
    return zone_type.ZoneType(name, weights, substitution, min_fraction, site_param_list)

def load_site_type(json_site_type):
    name = json_site_type["name"]
    legal_terrain = json_site_type["terrain"]
#    terrain_names = json_site_type["terrain"]
#    legal_terrain = []
#    for terrain_name in terrain_names:
#        legal_terrain.append(terrain.name_to_type[terrain_name])
        
    if "garrison" in json_site_type:
        garrison = json_site_type["garrison"]
        is_army = garrison["is_army"]
        leader_chance = garrison["leader_chance"] if is_army else 0
        depth = garrison.get("depth", 1)
        garrison_info = site_type.Garrison(is_army, garrison["min"], garrison["max"], leader_chance, depth)
    else:
        garrison_info = None
    if "loot" in json_site_type:
        loot = json_site_type["loot"]
        loot_effects = site_type.LootEffects(loot["status"], loot["gold"], loot["reputation"], loot["item"], loot["prisoner"])
    else:
        loot_effects = None
#    if "patrol" in json_site_type:
#        patrol = json_site_type["patrol"]
#        patrol_info = site_type.Patrol(patrol["chance_per_day"], patrol["range"], patrol["aggression"])
#    else:
#        patrol_info = None
#    
    if "spawn" in json_site_type:
        spawn = json_site_type["spawn"]
        print spawn
        spawn_info = site_type.Spawn(spawn["type"], spawn["chance_per_day"],  spawn["range"], spawn["aggression"], spawn.get("units", None))
    else:
        spawn_info = None
        
    owner = json_site_type["owner"]
    #site_type.owner_types[owner[0]] = owner[1]

    misc = json_site_type["misc"]
    misc_info = site_type.Misc("haven" in misc, "zone_center" in misc, misc["settlement_effect"], misc["income"], misc["reactivate_chance"])

    if name in DataLoader.name_makers:
        name_maker = DataLoader.name_makers[name]
    else:
        name_maker = None
    
    return site_type.SiteType(name, name_maker, owner, legal_terrain, garrison_info, spawn_info, loot_effects, misc_info)

def load_site_upgrades(json_site_upgrade):
    prereqs = json_site_upgrade.get("requires", None)
    
    return site_upgrade.SiteUpgrade(json_site_upgrade['name'], json_site_upgrade['site_types'], json_site_upgrade['min_level'],
                                     json_site_upgrade['cost'], prereqs, json_site_upgrade['effect'], json_site_upgrade['description'])

DataHandler = collections.namedtuple('DataHandler', ['filename', 'processor', 'dests', 'dest_types'])
class DataLoader(object):
  
    @classmethod
    def load_data(cls):
        cls.name_makers = {}
        #self.unit_types = {}
        cls.data_handlers = [DataHandler("names/site_names.json", load_name_maker, [cls.name_makers], ["Dict"]),
                             DataHandler("names/unit_names.json", load_name_maker, [cls.name_makers], ["Dict"]),
                             DataHandler("map/players.json", load_player_type, [player_type.npc_player_types], ["List"]),
                            # TODO: fix redundancy here, loading unit types twice: once to put in list, once to put in hash table by name
                             DataHandler("units/units.json", load_unit_type, 
                                         [unit.unit_types, unit.unit_types_by_name], ["List", "Dict"]),
#                             DataHandler("units/units.json", load_unit_type, unit.unit_types_by_name, "D"),
                             DataHandler("units/base items.json", load_base_items, [item.base_items], ["List"]),
                             DataHandler("units/item modifiers.json", load_item_mods, [item.item_modifiers], ["List"]),
                             DataHandler("map/site_types.json", load_site_type, [site_type.site_types], ["Dict"]),
                             DataHandler("map/site_upgrades.json", load_site_upgrades, 
                                         [site_upgrade.upgrades,site_upgrade.upgrades_by_name], ["List", "Dict"]),
#                             DataHandler("map/site_upgrades.json", load_site_upgrades, site_upgrade.upgrades_by_name, True),
                             DataHandler("map/zone_types.json", load_zone_type, [zone_type.zone_types], ["List"]),
                            DataHandler("units/hordes.json", load_horde_type, [group.horde_types_by_name], ["Dict"])]
        for data_handler in cls.data_handlers:
            json_file = open(os.path.join('data',data_handler.filename))
            print "loading " + data_handler.filename
            json_data = json.load(json_file) 
            for elem in json_data:
                processed_data = data_handler.processor(elem)
                for i in range(len(data_handler.dests)):
                    if data_handler.dest_types[i] == "Dict":
                        if isinstance(elem["name"], list):
                            for name in elem["name"]:
                                data_handler.dests[i][name] = processed_data
                        else:
                            data_handler.dests[i][elem["name"]] = processed_data
                    else:
                        data_handler.dests[i].append(processed_data)
            json_file.close()
    
        gen_prisoner_candidates(unit.unit_types, site_type.site_types, loot.prisoner_candidates)

    