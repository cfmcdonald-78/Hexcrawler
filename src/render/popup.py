'''
Created on Oct 13, 2012

@author: Chris
'''
import render.gui.modal as modal
import core.event_manager as event_manager

popup_events = [event_manager.SITE_REVOLT, event_manager.HERO_GRANTED]

class PopupRenderer(object):
    
    def __init__(self):
        event_manager.add_listener_multi(self.do_popup_event, popup_events)

    def set_data(self, map_data, mask):
        self.map_renderer = map_data
        self.curr_mask = mask

    def do_popup_event(self, event):
        if event.type == event_manager.SITE_REVOLT:
            if self.curr_mask.get_player() == event.data['former_owner']:
                site = event.data['site']
                self.create_popup("Revolt", site.get_name() + " has revolted\n against its occupiers", jump_to=site.get_hex())
        elif event.type == event_manager.HERO_GRANTED:
            if self.curr_mask.get_player() == event.data['player']:
                self.create_popup("Hero for Hire", "Attracted by your fame," "\na hero has arrived at \n" + 
                                  event.data['site_name'])
    def create_popup(self, title, text, jump_to=None):
        dialog = modal.TextDialog(title, text)
        # center map
        if jump_to != None and self.map_renderer != None:
            self.map_renderer.center(jump_to.x, jump_to.y) 
        dialog.show()
    
    
# if event.type == event_manager.LOOTING:
#            loc = event.data['hex_loc']
#            if self.mask != None and self.mask.get_player() == event.data['looting_player']: 
#               
#                loot_message = ""
#              
#                if event.data['gold'] != 0:
#                    loot_message += "\n    " + str(event.data['gold']) + " Gold"
#                if event.data['reputation'] != 0:
#                    loot_message +=  "\n    " + str(event.data['reputation']) + " Reputation"
#                if event.data['item_text'] != None:
#                    loot_message += "\n    Item: " + event.data['item_text']
#                if event.data['prisoner_text'] != None:
#                    loot_message += "\n    Prisoner: " + event.data['prisoner_text']
#              
#                if loot_message != "":
#                    # only display dialog if something actually looted
#                    loot_message = "While looting " + event.data['site_name'] + " you acquired: \n" + loot_message
#                    loot_dialog = modal.TextDialog("Loot", loot_message)
#                    loot_dialog.show()
#   elif self.is_shown() and event.type == event_manager.COMBAT_SPOILS:
#            spoils_message = "For defeating this foe you earned \n"
#            if event.data['reputation'] != 0:
#                spoils_message +=  "\n    " + str(event.data['reputation']) + " Reputation"
#            if event.data['item'] != None:
#                spoils_message += "\n    " + event.data['item'].get_name()
#            spoils_dialog = modal.TextDialog("Spoils", spoils_message)
#            spoils_dialog.show()