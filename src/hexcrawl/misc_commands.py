'''
Created on Jul 18, 2012

@author: Chris
'''
import core.command as command
import gamemap.site as site
from gamemap.site_type import site_types
import mob.group as group, mob.unit as unit, mob.trait as trait
from core.event_manager import Event
import core.event_manager as event_manager
import reputation
import gamemap.site_upgrade as site_upgrade

KEEP_COST_PER_LEVEL = 80
EMBASSY_COST_PER_LEVEL = 25

def get_build_cost(site_type_name, site_level):
    return KEEP_COST_PER_LEVEL * site_level

def get_embassy_cost(diplomat, site_level):
    return (EMBASSY_COST_PER_LEVEL + diplomat.get_group().get_owner().embassy_count()) * site_level

class BuildCommand(command.Command):
    '''
    classdocs
    '''

    def __init__(self, hex_loc, builder):
        super(BuildCommand, self).__init__()
        
        self.hex_loc = hex_loc
        self.builder = builder
    
    def validate(self, game):
        #TODO: validate that builder can build a site, and that this is a legit location for it
        return True
    
    def execute(self, game):
        build_hex = game.get_map().get_hex(self.hex_loc.x, self.hex_loc.y)
        active_group = build_hex.active_group
        player = active_group.get_owner()
        
        site_type_name = self.builder.trait_value(trait.BUILD)
        
        cost = get_build_cost(site_type_name, self.builder.get_level())
        if player.get_gold() >= cost:
            player.adjust_gold(-cost)
            site_type = site_types[site_type_name]
            new_site = site.Site(build_hex, site_type, self.builder.get_level(), player, default_owner=game.npc_table[site_type.owner_name]) 
            new_site.initialize()
#            player.add_site(new_site)
            build_hex.site = new_site
            new_site.spread_settlement(game.get_map())
        
            # builder is consumed by act of building
            active_group.remove_unit(self.builder)
            active_group.check_elimination()
            
            # rep. adjustment for building site is reverse of what you'd get for taking it over
            reputation.adjust_reputation(reputation.BUILT_SITE, new_site, player)


class EmbassyCommand(command.Command):
    '''
    classdocs
    '''

    def __init__(self, hex_loc, diplomat):
        super(EmbassyCommand, self).__init__()
        
        self.hex_loc = hex_loc
        self.diplomat = diplomat
    
    def validate(self, game):
        #TODO: validate that command is legit
        return True
    
    def execute(self, game):
        embassy_hex = game.get_map().get_hex(self.hex_loc.x, self.hex_loc.y)
        active_group = embassy_hex.active_group
        player = active_group.get_owner()
        embassy_site = embassy_hex.site
#        site_type_name = self.builder.trait_value(unit.BUILD)
        
        cost = get_embassy_cost(self.diplomat, embassy_site.get_level())
        if player.get_gold() >= cost:
            player.adjust_gold(-cost)
#            player.adjust_embassy(embassy_site)

            embassy_site.set_embassy(player)

            # diplomat is consumed by act of building embassy
            active_group.remove_unit(self.diplomat)
            active_group.check_elimination()
            

class UpgradeCommand(command.Command):
    def __init__(self, target_site, upgrade_name):
        super(UpgradeCommand, self).__init__()
        
        self.site = target_site
        self.upgrade_name = upgrade_name
    
    def validate(self, game):
        if self.upgrade_name not in [upgrade.name for upgrade in site_upgrade.available_upgrades(self.site)]:
            return False

        upgrade = site_upgrade.upgrades_by_name[self.upgrade_name]
        self.cost = upgrade.get_cost(self.site)
        if self.site.get_owner().get_gold() < self.cost:
            return False
    
        # TODO: validate prereqs
        
        return True
        
    def execute(self, game):
        self.site.add_upgrade(self.upgrade_name)
        self.site.get_owner().adjust_gold(-self.cost)
        garrison = self.site.get_hex().get_garrison()
        if garrison != None:
            garrison.update_trait_effects()
        self.site.adjust_income(game.get_map()) # some upgrades effect income, so adjust it
        event_manager.queue_event(Event(event_manager.SITE_UPGRADED, [self.site, self.upgrade_name]))
        

class HireCommand(command.Command):
    pass


class UnitTransferCommand(command.Command):
    
    def __init__(self, hex_loc, to_garrison, index):
        self.hex_loc = hex_loc
        self.to_garrison = to_garrison
        self.index = index
        
    def validate(self, game):
        self.hex = game.get_map().get_hex(self.hex_loc.x, self.hex_loc.y)
        if self.hex == None or not self.hex.has_site():
            return False
        
        if self.hex.site.get_owner() != game.get_curr_player():
            return False

        if self.hex.get_active_group() != None and self.hex.get_active_group().get_owner() != game.get_curr_player():
            return False
   
        self.source, self.dest = self.hex.get_garrison(), self.hex.get_active_group()
        if self.to_garrison:
            self.source, self.dest = self.dest, self.source
            
        # must be enough room in target group
        if self.dest != None and self.dest.is_full():
            return False
        
        # must be a unit in the right place for the transfer!
        if self.source == None or self.source.num_units() <= self.index:
            return False
   
        return True
    
    def execute(self, game):
        transfer_unit = self.source.remove_unit_at_index(self.index, transfer=True)
        if self.dest == None:
            self.dest = group.Group(game.get_curr_player())
            self.dest.add_unit(transfer_unit, transfer=True)
            if self.to_garrison:
                self.hex.add_garrison(self.dest)
            else:
                self.hex.add_group(self.dest)
        else:
            self.dest.add_unit(transfer_unit, transfer=True)
        self.source.check_elimination()

class ItemTransferCommand(command.Command):
    
    def __init__(self, unit, from_backpack, index):
        self.unit = unit
        self.from_backpack = from_backpack
        self.index = index
        
    def validate(self, game):
        transfer_item = self.unit.get_backpack_item(self.index) if self.from_backpack else self.unit.get_equipped_item(self.index) 
        if transfer_item == None:
            return False
        if self.from_backpack:
            return self.unit.can_equip_item(transfer_item)
        else:
            return self.unit.can_unequip_item()
        
    def execute(self, game):
        if self.from_backpack:
            self.unit.equip_item(self.unit.get_backpack_item(self.index))
        else:
            self.unit.unequip_item(self.unit.get_equipped_item(self.index))
        event_manager.queue_event(Event(event_manager.ITEM_SHIFTED, [self.unit]))

class UnitDisbandCommand(command.Command):
    
    def __init__(self, remove_group, index):
        self.remove_group = remove_group
        self.remove_index = index
         
    def validate(self, game):
        return self.remove_group.num_units() > self.remove_index
         
    def execute(self, game):
        disband_unit = self.remove_group.get_unit(self.remove_index)
        self.remove_group.remove_unit(disband_unit)
        disband_unit.disband()
        self.remove_group.check_elimination()
        
class UnitShiftCommand(command.Command):
    
    def __init__(self, shift_group, old_index, new_index):
        self.group = shift_group
        self.old_index = old_index
        self.new_index = new_index
         
    def validate(self, game):
        if self.group.dead_unit_crossing(self.old_index, self.new_index):
            return False
        
        return (0 <= self.old_index <= self.group.num_units()) and (0 <= self.new_index <= self.group.num_units())
         
    def execute(self, game):
        self.group.move_unit(self.old_index, self.new_index)
        event_manager.queue_event(Event(event_manager.UNIT_SHIFTED, [self.group, self.old_index, self.new_index]))

class ItemSellCommand(command.Command):
    def __init__(self, unit, from_backpack, index):
        self.unit = unit
        self.from_backpack = from_backpack
        self.index = index
        
    def validate(self, game):
        # TODO: validate location - must be on an active site
        return self.unit.get_backpack_item(self.index) != None if self.from_backpack else self.unit.get_equipped_item(self.index) != None
    
    def execute(self, game):
        if self.from_backpack:
            sold_item = self.unit.get_backpack_item(self.index)
        else:
            sold_item = self.unit.get_equipped_item(self.index)
        
        self.unit.get_owner().adjust_gold(sold_item.get_gold_value())
        self.unit.discard_item(sold_item)
        event_manager.queue_event(Event(event_manager.ITEM_REMOVED, [self.unit]))

class UseTraitCommand(command.Command):
    def __init__(self, using_unit, used_trait):
        self.unit = using_unit
        self.trait = used_trait
    
    def validate(self, game):
        return self.trait in trait.useable_traits and self.unit.trait_value(self.trait) > 0
    
    def execute(self, game):
        self.unit.use_trait(self.trait)
    
class ItemDiscardCommand(command.Command):
    def __init__(self, unit, from_backpack, index):
        self.unit = unit
        self.from_backpack = from_backpack
        self.index = index
        
    def validate(self, game):
        return self.unit.get_backpack_item(self.index) != None if self.from_backpack else self.unit.get_equipped_item(self.index) != None
    
    def execute(self, game):
        if self.from_backpack:
            self.unit.discard_item(self.unit.get_backpack_item(self.index))
        else:
            self.unit.discard_item(self.unit.get_equipped_item(self.index))
        event_manager.queue_event(Event(event_manager.ITEM_REMOVED, [self.unit]))

class EndTurnCommand(command.Command):
    
    def __init__(self, ending_player):
        self.player = ending_player
        
    def validate(self, game):
        #TODO: validation
        return self.player == game.get_curr_player() 
    
    def execute(self, game):
        game.advance_turn()
        
        
