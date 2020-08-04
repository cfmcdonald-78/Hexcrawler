'''
Created on Jul 2, 2012

@author: Chris
'''
import core.event_manager as event_manager
import image
import gui.component as component
from gui.label import Label
from util.tools import Rect
import text 
import gamemap.mask as mask

class StatusRenderer(component.Window):
    '''
    classdocs
    '''

    def __init__(self, position_rect):
        super(StatusRenderer, self).__init__(position_rect)
        self.pad = 4
        self.last_event = None
        event_manager.add_listener(self.handle_events, event_manager.DAY_START)
        event_manager.add_listener(self.handle_events, event_manager.RANDOM_EVENT)
        event_manager.add_listener(self.handle_events, event_manager.PLAYER_STATUS_CHANGE)
        event_manager.add_listener(self.handle_events, event_manager.HEX_SELECTED)
        
#        x = self.rect.x + 164 + 2*(image.UI_ICON_WIDTH + 10)
#        y = self.rect.y + 8
       
        
        x = self.rect.x + 114 + image.UI_ICON_WIDTH 
        y = self.rect.y + self.pad
        width = 50
        height = self.rect.height - self.pad
        self.gold_label = Label(Rect(x, y, width, height), "", font=text.lg_font)
        x += image.UI_ICON_WIDTH + 55
        self.income_label = Label(Rect(x, y, width, height), "", font=text.lg_font)
        x += image.UI_ICON_WIDTH + 55
        self.rep_label = Label(Rect(x, y, width, height), "", font=text.lg_font)
        x += image.UI_ICON_WIDTH + 53
        self.fame_label = Label(Rect(x, y, width, height), "", font=text.lg_font)
        
        x += 400
        self.zone_label = Label(Rect(x, y, width, height), "", font=text.lg_font)
        
        self.add_child(self.income_label)
        self.add_child(self.gold_label)
        self.add_child(self.rep_label)
        self.add_child(self.fame_label)
        self.add_child(self.zone_label)
        
        #self.turn_label = self.font.render("Turn:", True, (255, 255, 255), (25, 25, 25))
        #self.gold_label = self.font.render("Gold:", True, (255, 255, 255), (25, 25, 25))
        #self.rep_label = self.font.render("Reputation:", True, (255, 255, 255), (25, 25, 25))
    
    def set_data(self, map_data, curr_player, curr_mask, curr_turn):
        self.map_data = map_data
        self.curr_player = curr_player
        self.mask_player = curr_mask.get_player()
#        self.curr_mask = curr_mask
        self.turn = curr_turn
        self.update_labels()
    
    def gen_tool_tip(self, top_label, value_dict):
        tool_tip_text = top_label + "\n"
        for key_name in value_dict:
            tool_tip_text += "\n" + key_name + ": " + str(value_dict[key_name])
        return tool_tip_text
    
    def update_labels(self):
        tool_tip_text = self.gen_tool_tip("Income", self.mask_player.income_by_type)
        self.income_label.set_label(str(self.mask_player.get_income()), tool_tip_text=tool_tip_text)
        
        self.gold_label.set_label(str(self.mask_player.get_gold()))
        
        tool_tip_text = self.gen_tool_tip("Reputation", self.mask_player.reputation_by_type)
        self.rep_label.set_label(str(self.mask_player.get_reputation()), tool_tip_text=tool_tip_text)
    
        tool_tip_text = self.gen_tool_tip("Fame", self.mask_player.fame_by_type)
        self.fame_label.set_label(str(self.mask_player.get_fame()), tool_tip_text=tool_tip_text)
    
    def handle_events(self, event):
        if event.type == event_manager.DAY_START:
            self.last_event = None  # clear event display at start of each day
        elif event.type == event_manager.RANDOM_EVENT:
            self.last_event = event.data['description']
#        elif event.type == event_manager.PLAYER_WON:
#            self.last_event = "Game Over: " + event.data['player'].get_name() + " Won"
#        elif event.type == event_manager.PLAYER_LOST:
#            self.last_event = "Loss: " + event.data['player'].get_name() + " Lost"
        elif event.type == event_manager.PLAYER_STATUS_CHANGE:
            self.update_labels()
        elif event.type == event_manager.HEX_SELECTED:
            x, y = event.data['loc']
            if self.mask_player.get_mask().get_visibility(x, y) == mask.NEVER_VISIBLE:
                label_text = ""
            else:
                hex_zone = self.map_data.get_zone(x, y)
                label_text = hex_zone.name + " (" + hex_zone.get_type().name + ")"
        
            self.zone_label.set_label(label_text)
           
    def render(self, surface, images):
        super(StatusRenderer, self).render(surface, images)
        x = self.rect.x + 64
        y = self.rect.y + self.rect.height / 2
        #surface.blit(self.turn_label, (x, y))
        #x += self.turn_label.get_width() + 4
        images.text.draw_text("Week " + str(self.turn.week) + ", Day " + str(self.turn.day), 
                              text.lg_font, x, y, surface)
        #turn_text =  image.lg_font.render("Week " + str(turn.week) + ", Day " + str(turn.day), True, (255, 255, 255), (25, 25, 25))
        #surface.blit(turn_text, (x, y))
        x += 60
         
#        if self.curr_player.is_actor(): 
            #surface.blit(self.gold_label, (x, y))
            #x += self.gold_label.get_width() + 4
            #image.text.draw_text("Gold : " + str(curr_player.get_gold()), image.text.lg_font, x, y, surface)
        surface.blit(images.gold, (x, y - self.rect.height / 2))
        x += image.UI_ICON_WIDTH + 10
#        images.text.draw_text(str(self.curr_player.get_gold()), images.text.lg_font, x, y, surface, color=text.LIGHT)
        x += 50
            
        surface.blit(images.income, (x, y - self.rect.height / 2)) 
#            images.text.draw_text(str(self.curr_player.get_income()), images.text.lg_font, x, y, surface, color=text.LIGHT)
        x += 50 + image.UI_ICON_WIDTH + 10
            #surface.blit(self.rep_label, (x, y))
            #x += self.rep_label.get_width() + 4
        surface.blit(images.reputation, (x, y - self.rect.height / 2))
        x += 50 + image.UI_ICON_WIDTH
        
        surface.blit(images.fame, (x, y - self.rect.height / 2))
        x += image.UI_ICON_WIDTH + 10
#        images.text.draw_text(str(self.curr_player.get_reputation()), images.text.lg_font, x, y, surface, color=text.LIGHT)

        x = self.rect.x + self.rect.width / 2
        images.text.draw_text(self.curr_player.get_name(), text.vlg_font, x, y, surface)
        
        if self.last_event != None:
            x = self.rect.x + self.rect.width / 2
            y += 30
            images.text.draw_text(self.last_event, text.sm_font, x, y, surface, color=text.LIGHT)
            
    
        
        
        
        