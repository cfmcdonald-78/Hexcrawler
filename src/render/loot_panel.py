'''
Created on Jul 2, 2012

@author: Chris
'''
import hexcrawl.loot as loot, gamemap.mask as mask
import core.event_manager as event_manager
import gui.component as component
import gui.modal as modal
import text

#loot_event_types = [event_manager.LOOT_START, event_manager.LOOT_GOLD, event_manager.LOOT_PRISONER, event_manager.LOOT_ITEM, 
#                      event_manager.LOOT_REPUTATION, event_manager.LOOT_END]

class LootRenderer(component.Window):
    '''
    classdocs
    '''


    def __init__(self, position_rect):
        super(LootRenderer, self).__init__(position_rect, True)
#        self.active = False
        self.mask = None
#        self.pad = 20
#        #self.looting_label = self.font.render("Looting ", True, (255, 255, 255), (25, 25, 25))
#        self.gold_label = text.lg_font.render("Gold:", True, (255, 255, 255), (25, 25, 25))
#        self.prisoner_label = text.lg_font.render("Prisoner:", True, (255, 255, 255), (25, 25, 25))
#        self.item_label = text.lg_font.render("Item:", True, (255, 255, 255), (25, 25, 25))
#        self.reputation_label = text.lg_font.render("Reputation:", True, (255, 255, 255), (25, 25, 25))
    
#        for event_type in loot_event_types:
        event_manager.add_listener(self.handle_game_events, event_manager.LOOTING)
    
    def set_data(self, curr_mask):
        self.mask = curr_mask
    
#    def is_active(self):
#        return self.active
    
    def handle_game_events(self, event):
        if event.type == event_manager.LOOTING:
            loc = event.data['hex_loc']
            if self.mask != None and self.mask.get_player() == event.data['looting_player']: 
               
                loot_message = ""
              
                if event.data['gold'] != 0:
                    loot_message += "\n    " + str(event.data['gold']) + " Gold"
                if event.data['reputation'] != 0:
                    loot_message +=  "\n    " + str(event.data['reputation']) + " Reputation"
                if event.data['item_text'] != None:
                    loot_message += "\n    Item: " + event.data['item_text']
                if event.data['prisoner_text'] != None:
                    loot_message += "\n    Prisoner: " + event.data['prisoner_text']
              
                if loot_message != "":
                    # only display dialog if something actually looted
                    loot_message = "While looting " + event.data['site_name'] + " you acquired: \n" + loot_message
                    loot_dialog = modal.TextDialog("Loot", loot_message)
                    loot_dialog.show()
        
        
#        if event.type == event_manager.LOOT_START:
#            loc = event.data['hex_loc']
#            if self.mask != None and self.mask.get_visibility(loc.x, loc.y) == mask.VISIBLE: 
#                self.show()
##                self.active = True
#                self.gold_text = ""
#                self.prisoner_text = ""
#                self.item_text = ""
#                self.reputation_text = ""
#                self.title_text = "Looting " + event.data['site_name']   
#        elif self.is_shown() and event.type == event_manager.LOOT_END:
#            self.hide()
##            self.active = False
#        elif self.is_shown():
#            if event.type == event_manager.LOOT_GOLD:
#                self.gold_text = str(event.data['amount'])
#            elif event.type == event_manager.LOOT_PRISONER:
#                self.prisoner_text = event.data['name'] 
##                if prisoner_name == None:
##                    self.prisoner_text = "None"
##                else:
##                    self.prisoner_text = prisoner_name + " Freed"
#            elif event.type == event_manager.LOOT_ITEM:
#                item_name = event.data['name'] 
#                if item_name == None:
#                    self.item_text = "None"
#                else:
#                    self.item_text += item_name + " Found"
#            elif event.type == event_manager.LOOT_REPUTATION:
#                amount = event.data['amount']
#                sign = "+" if amount > 0 else ""
#                self.reputation_text = str(sign + str(amount)) 
#                
#        
#    def render(self, surface, images):
#        super(LootRenderer, self).render(surface, images)
##        if not self.is_active():
##            return
#        
##        surface.fill((160, 82, 45), self.rect)
##        images.draw_window(surface, self.rect)
#        
#        x = self.rect.x + self.rect.width / 2
#        y = self.rect.y + self.pad
#        images.text.draw_text(self.title_text, text.vlg_font, x, y, surface)
#        
#        # Headings
#        x = self.rect.x + self.pad
#        y = self.rect.y + text.lg_font.get_height() + self.pad * 2
#        surface.blit(self.gold_label, (x, y))
#        x += self.rect.width / 4
#        surface.blit(self.prisoner_label, (x, y))
#        x += self.rect.width / 4
#        surface.blit(self.item_label, (x, y))
#        x += self.rect.width / 4
#        surface.blit(self.reputation_label, (x, y))
#        
#        # Status updates
#        x = self.rect.x + self.pad
#        y += self.pad * 2
#        images.text.draw_text(self.gold_text, text.lg_font, x, y, surface)
#        x += self.rect.width / 4
#    
#        images.text.draw_text(self.prisoner_text, text.lg_font, x, y, surface)
#
#        x += self.rect.width / 4
#        images.text.draw_text(self.item_text, text.lg_font, x, y, surface)
#        x += self.rect.width / 4
#        
#        images.text.draw_text(self.reputation_text, text.lg_font, x, y, surface)
#
#        