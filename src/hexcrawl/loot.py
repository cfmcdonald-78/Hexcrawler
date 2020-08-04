'''
Created on Jul 2, 2012

@author: Chris
'''
import gamemap.site_type as site_type, mob.unit as unit, reputation, mob.item as item, mob.trait as trait
import random
from core.process_manager import StepProcess
import core.event_manager as event_manager
from core.event_manager import Event


prisoner_candidates = {}


class Loot(object):
    '''
    classdocs
    '''

def average_looting(loot_site, looters):
    total_looting, num_looters = 0, 0
        
    for i in range(looters.num_units()):
        looter = looters.get_unit(i)
        # army units can't loot in tight quarters areas
        if not loot_site.is_tight_quarters() or not looter.is_army():
            total_looting += looter.get_looting()
            num_looters += 1
        
    return 0 if num_looters == 0 else total_looting / float(num_looters)

def compute_gold(loot_site, looters):
    # gold haul scaled according to average looting score of looting group
    return int(loot_site.base_gold * average_looting(loot_site, looters))

def look_for_prisoner(loot_site, looters):
    prisoner_type = loot_site.site_type.loot_effects.prisoner
    if prisoner_type == site_type.NO_PRISONER:
        return None
    
#    if loot_site.get_fixed_prisoner() != None:
#        # if prisoner pre-set (e.g. by "hero in chains" event), use that one
#        return loot_site.get_fixed_prisoner()
    
    # chance for higher level prisoner with good looting
    bonus_level =  1 if random.random() <= ((average_looting(loot_site, looters) - 1) / float(3)) else 0
    
    prisoner_types = [prisoner for prisoner in prisoner_candidates[prisoner_type] if (prisoner.level == (loot_site.level + bonus_level) and 
                                                                          (not prisoner.is_army or not loot_site.is_tight_quarters()))]
  
#    if loot_site.site_type.loot_effects.prisoner == site_type.VILLAIN_PRISONER:
#        prisoner_types = [prisoner for prisoner in prisoner_types if prisoner.traits.get(trait.REPUTATION, 0) < 0]
#    else:
#        prisoner_types = [prisoner for prisoner in prisoner_types if not (prisoner.traits.get(trait.REPUTATION, 0) < 0)]
    if len(prisoner_types) == 0:
        return None
        
    return unit.Unit(random.choice(prisoner_types))

def look_for_item(loot_site, looters):
    if loot_site.site_type.loot_effects.item == site_type.NO_ITEM:
        return None
    
    # chance for higher level item with good looting
    bonus_level =  1 if random.random() <= ((average_looting(loot_site, looters) - 1) / float(3)) else 0

    return item.random_item(loot_site.level + bonus_level, loot_site.site_type.loot_effects.item) 

def compute_rep_change(loot_site, looters):
    
    return reputation.adjust_reputation(reputation.LOOTED_SITE, loot_site, looters.get_owner())
        
def update_site_status(loot_site, looters):
    new_status = loot_site.site_type.loot_effects.new_status
    
    if new_status == site_type.DESTROYED:
        loot_site.destroy()
    elif new_status == site_type.SACKED or looters.has_trait(trait.PILLAGER):
        # monsters don't take over anything, just smash it.  Reverts to original owner.
        loot_site.sack()
    elif new_status == site_type.ACTIVE:
        # transfer site from  old to new owner
        loot_site.transfer(looters.get_owner())
    
def do_loot(loot_hex, looters):
    loot_site = loot_hex.site
    
    gold_amount = 0
    reputation_adj = 0
    item_name = None
    prisoner_name = None
        
    if looters.get_owner().is_actor():    
        gold_amount = compute_gold(loot_site, looters)
        looters.owner.adjust_gold(gold_amount)
    
        prisoner = look_for_prisoner(loot_site, looters)  
        if prisoner != None:
                prisoner_name = prisoner.get_name()
                if prisoner.get_level() > loot_site.get_level():
                    # bonus!
                    prisoner_name += " *"
                if looters.is_full():
                    prisoner_name += ", but no room"
                else:  
                    will_join, reason = prisoner.will_join(looters.get_owner())   
                    if will_join:                 
                        looters.add_unit(prisoner)
                    else:
                        prisoner_name += ", but " + reason
    
        item = look_for_item(loot_site, looters)
        if item != None:
            item_name = item.get_name()
            if item.get_level() > loot_site.get_level():
                # bonus!
                item_name += " *"
            if not looters.add_item(item):
                item_name += ", but no one to carry it"
        
        reputation_adj = compute_rep_change(loot_site, looters)
        
    update_site_status(loot_site, looters)
    
    event_manager.queue_event(Event(event_manager.LOOTING, [looters.get_owner(), loot_hex, loot_site.get_name(), 
                                                            gold_amount, reputation_adj, item_name, prisoner_name]))
    event_manager.queue_event(Event(event_manager.SITE_LOOTED, [looters.get_owner(), loot_site]))
    return
