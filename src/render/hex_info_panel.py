'''
Created on Jun 29, 2012

@author: Chris
'''

from util.tools import *
import group_panel, image, gamemap.mask as mask 
from gui.button import Toggle, Button
from gui.upgrade_dialog import UpgradeDialog
from gui.label import Label
import gui.component as component
from core.event_manager import Event
import core.event_manager as event_manager
import text
import mob.move_mode as move_mode

import gamemap.site_type as site_type

#UnitSelection = collections.namedtuple('UnitSelection', ['group_index', 'unit_index'])

class HexInfoRenderer(component.Window):
    '''
    panel that renders info about selected hex, including any site there, any active
    group of characters/units, and garrison, and any units available for hire.
    '''


    def __init__(self, position_rect, images):
        super(HexInfoRenderer, self).__init__(position_rect)

        self.engineering_active = False
        self.selected_hex = None
     
        # probably need to allow for some padding in these calculations
        self.site_rect = Rect(self.rect.x, self.rect.y, self.rect.width / 4, self.rect.height)
        
        def hire_callback(toggle_down):
            if toggle_down:
                self.for_hire_renderer.show()
                self.garrison_renderer.hide()
            else:
                self.for_hire_renderer.hide()
                self.garrison_renderer.show()
    
        def upgrade_callback():
            upgrade_dialog = UpgradeDialog(250, 300, "Site Upgrades", self.selected_hex.site)
            upgrade_dialog.show()
    
        x, y = self.site_rect.x + self.site_rect.width / 4, self.site_rect.y + (self.site_rect.height * 3) / 4
        width, height = self.site_rect.width / 4, self.site_rect.height / 8
        self.upgrade_button = Button(Rect(x, y, width, height), "Upg.",  upgrade_callback)
        
        self.hire_button = Toggle(Rect(x + width + 8, y, width, height), "Hire",  hire_callback)
       
        self.add_child(self.hire_button)
        self.add_child(self.upgrade_button)
      
        active_group_rect = Rect(self.rect.x + self.site_rect.width, self.rect.y + 1, 
                                      (3 * self.rect.width) /4 , image.UNIT_HEIGHT + 8)
        self.active_group_renderer = group_panel.OccupantRenderer("Active", active_group_rect, False)
        
        x = active_group_rect.x + (active_group_rect.width) / 2
        y = active_group_rect.y + active_group_rect.height + 12
        
        def transfer_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 't', key = 't')
            
        self.transfer_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.transfer,  
                                      transfer_callback,  image_label = True,  tool_tip_text = "transfer (t)")
        x += image.SM_BUTTON_WIDTH + 4
        
        def disband_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 'x', key = 'x')
        
        self.disband_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.disband,  
                                     disband_callback, image_label = True,  tool_tip_text = "disband (x)")
        self.add_child(self.transfer_button)
        self.add_child(self.disband_button)
        self.transfer_button.hide()
        self.disband_button.hide()
        
        y =  self.disband_button.rect.y + self.disband_button.rect.height + 2
        
        second_group_rect  = Rect(self.rect.x + self.site_rect.width, y, 
                                   (3 * self.rect.width) /4, self.rect.height - (y - self.rect.y))
        self.garrison_renderer = group_panel.OccupantRenderer("Garrison", second_group_rect, True)
        self.for_hire_renderer = group_panel.HireRenderer("Hire", second_group_rect)
        
        self.add_child(self.active_group_renderer)
        self.add_child(self.garrison_renderer)
        self.add_child(self.for_hire_renderer)
        self.garrison_renderer.set_partner(self.active_group_renderer)
        self.active_group_renderer.set_partner(self.garrison_renderer)
        
        x = self.rect.x + 34 + image.UI_ICON_WIDTH + 25
        y = self.rect.y + 50 + image.UNIT_HEIGHT
        self.revolt_icon = Label(Rect(x, y, image.UI_ICON_WIDTH, image.UI_ICON_HEIGHT), images.revolt, image_label = True,
                                 tool_tip_text = "Revolt chance,\nchecked at week start")
        
        event_manager.add_listener(self.handle_game_events, event_manager.HEX_SELECTED)

    def handle_game_events(self, event):
        if event.type == event_manager.HEX_SELECTED:
            self.set_hex( event.data['loc'] )
        
    def set_data(self, map_data, curr_player, curr_mask):
        self.map_data = map_data
        self.curr_mask = curr_mask
        self.curr_player = curr_player
        # reselect hex to reset what's shown according to new player data
        self.set_hex(self.selected_hex)
   
    def deselect_all(self):
        self.active_group_renderer.mark_selected(None)
        self.garrison_renderer.mark_selected(None)
        self.for_hire_renderer.mark_selected(None)
    
    def set_hex(self, new_hex_loc):
        self.deselect_all()
        self.upgrade_button.hide()
        self.hire_button.hide()
        self.hire_button.reset()
        self.engineering_active = False
        if new_hex_loc == None:
            return
            
        self.selected_hex = self.map_data.get_hex(new_hex_loc.x, new_hex_loc.y)
        if self.selected_hex == None:
            return
        
        
        self.active_group_renderer.set_data(self.selected_hex, self.curr_player, self.curr_mask)
        if self.selected_hex.deep_garrison():
            self.garrison_renderer.set_data(None, self.curr_player, self.curr_mask)
        else:
            self.garrison_renderer.set_data(self.selected_hex, self.curr_player, self.curr_mask)
        
      
        self.for_hire_renderer.set_data(self.selected_hex, self.curr_player, self.curr_mask)
        self.for_hire_renderer.hide()
        
        if  self.curr_mask.get_visibility(self.selected_hex.x, self.selected_hex.y) == mask.VISIBLE:
            self.active_group_renderer.show()
            self.garrison_renderer.show()
        else:
            self.active_group_renderer.hide()
            self.garrison_renderer.hide()
          
        if  self.selected_hex.has_site() and self.selected_hex.site.hireable_by(self.curr_player):
            self.hire_button.show()
            
        if self.selected_hex.has_site() and self.selected_hex.site.get_owner() == self.curr_player:
            self.upgrade_button.show()  
            if self.selected_hex.get_active_group() != None:
                self.transfer_button.show()
                self.disband_button.show()
            else:
                self.transfer_button.hide()
                self.disband_button.hide()
        else:
                self.transfer_button.hide()
                self.disband_button.hide()
        
        self.add_child(self.revolt_icon)
        self.revolt_icon.hide()


    def event_handler(self, event):
        if event.type == component.MOUSE_CLICK:
            self.deselect_all()
            return True 
        
        return super(HexInfoRenderer, self).event_handler(event) 
    
    def render_site(self, surface, images, active_site, curr_player, mask_player):
            x = self.site_rect.x + (self.site_rect.width / 2)
            y = self.site_rect.y + 14
            images.text.draw_text(active_site.get_name(), text.lg_font, x, y, surface)
            
            y += 16
            images.text.draw_text("Lv. " +  str(active_site.level) + " " + active_site.site_type.name,  text.sm_font, x, y, surface)
            y += 16
            
            if active_site.status == site_type.SACKED:
                status_text = "Sacked"
            else:
                status_text = active_site.owner.get_name()
            
            images.text.draw_text(status_text, text.sm_font, x, y, surface)
#   
            y += 10
            x -= image.UNIT_WIDTH / 2
            images.draw_site(active_site, surface, mask_player, (x, y))
            
            y += image.UNIT_HEIGHT - 10
            icon_y = y
            x = self.rect.x + 30
            if active_site.is_active() and active_site.get_income() != 0:
                surface.blit(images.income, (x, y))
                x += image.UI_ICON_WIDTH + 10
                y += image.UI_ICON_WIDTH /2 
                images.text.draw_text(str(active_site.get_income()), text.sm_font, x, y, surface)
            x = self.rect.x + 34 + image.UI_ICON_WIDTH + 25
            y = icon_y
            if active_site.is_active() and active_site.revolt_chance() != 0:
                self.revolt_icon.show()
                x = self.revolt_icon.rect.x + image.UI_ICON_WIDTH + 16
                y = self.revolt_icon.rect.y + image.UI_ICON_WIDTH /2 
                images.text.draw_text(str(int(active_site.revolt_chance() * 100)) + "%", text.sm_font, x, y, surface)
            else:
                self.revolt_icon.hide()
    
    def render(self, surface, images):
        super(HexInfoRenderer, self).render(surface, images)

        if self.selected_hex == None:
            return
        
        mask_state = self.curr_mask.get_visibility(self.selected_hex.x, self.selected_hex.y)
        
        if mask_state == mask.NEVER_VISIBLE:
            return
    
        # render site info
        active_site = self.selected_hex.site
        if active_site != None:
            self.render_site(surface, images, active_site, self.curr_player, self.curr_mask.get_player())

        # render groups in hex  
        active_group = self.selected_hex.active_group
        if active_group != None and mask_state == mask.VISIBLE:

            x, y = self.active_group_renderer.rect.x + 4, self.active_group_renderer.rect.y + 24
            if active_group.get_move_mode() == move_mode.NAVAL:
                surface.blit(images.naval_move, (x, y))
            else:
                surface.blit(images.foot_move, (x, y))
            images.text.draw_text(str(active_group.get_moves_left()), text.lg_font, x + image.UI_ICON_WIDTH + 10,
                                  y + (image.UI_ICON_HEIGHT / 2), surface)
            
            if active_group.get_owner() == self.curr_player:
                x = self.rect.x + (5 * self.rect.width) / 8
                y = self.rect.y + self.rect.height / 2

      
            