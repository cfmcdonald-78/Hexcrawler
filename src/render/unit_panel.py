'''
Created on Aug 5, 2012

@author: Chris
'''
import image, item_panel
from util.tools import  Rect
from gui.button import Button
from gui.label import Label
from core.event_manager import Event
import core.event_manager as event_manager
import gui.component as component
import mob.unit as unit, mob.move_mode as move_mode, mob.trait as trait
import hexcrawl.misc_commands as misc_commands
import gamemap.site_type as site_type
import text

class UnitRenderer(component.Window):
    

    def __init__(self, position_rect, images):
        super(UnitRenderer, self).__init__(position_rect)
        self.selected_unit = None
        
        def item_callback():
            item_dialog = item_panel.ItemDialog(325, 325, "Items", self.selected_unit, self.can_sell_items, images)
            item_dialog.show()
        
        x, y = self.rect.x + self.rect.width / 3, self.rect.y + (self.rect.height * 3)/ 4
        width, height =  (self.rect.width) / 2, self.rect.height / 8
        self.item_button = Button( Rect(x, y, width, height), "Items", item_callback)
        
        def build_callback():
            command = misc_commands.BuildCommand(self.select_hex, self.selected_unit)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
        
        self.build_button = Button( Rect(x, y, width, height), "", build_callback)
        
        def embassy_callback():
            command = misc_commands.EmbassyCommand(self.select_hex, self.selected_unit)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
        
        self.embassy_button = Button( Rect(x, y, width, height), "", embassy_callback)
        
        self.can_sell_items = False
        self.map_data = None
        
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_SELECTED)
        event_manager.add_listener(self.handle_game_events, event_manager.HEX_SELECTED)
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_STATS_CHANGED)
    
    def set_data(self, map_data, image_data):
        self.map_data = map_data
        self.image_data = image_data
    
    def handle_game_events(self, event):
        if event.type == event_manager.HEX_SELECTED:
            hex_loc = event.data['loc']
            self.select_hex = self.map_data.get_hex(hex_loc.x, hex_loc.y)
            self.can_sell_items = self.select_hex != None and self.select_hex.has_site() and self.select_hex.site.is_active()
        if event.type == event_manager.UNIT_SELECTED:
            self.set_selected( event.data['unit'] )
        if event.type == event_manager.UNIT_STATS_CHANGED:
            self.set_selected(self.selected_unit)
        
    def is_active(self):
        return self.selected_unit != None
    
    def can_embassy(self):
        if self.selected_unit == None or self.select_hex == None:
            return False
        
        if not self.selected_unit.has_trait(trait.DIPLOMAT) or not self.selected_unit.get_owner():
            return False
        
        if not self.select_hex.has_site():
            return False
        
        embassy_site = self.select_hex.site
        
        if embassy_site.get_level() > self.selected_unit.trait_value(trait.DIPLOMAT):
            return False
        
        if embassy_site.get_embassy() != None:
            return False
        
        return True
    
    def can_build(self):
        if self.selected_unit == None or self.select_hex == None:
            return False
        
        if not self.selected_unit.has_trait(trait.BUILD) or not self.selected_unit.get_owner():
            return False
        
        # can't build too close to another site
        if self.select_hex.has_site():
            return False
        neighbors = self.map_data.get_neighbors(self.select_hex.x, self.select_hex.y)
        for neighbor in neighbors:
            if neighbor.has_site():
                return False
        
        build_type = self.selected_unit.trait_value(trait.BUILD)
        
        # can only build in legit terrain
        curr_site_type = site_type.site_types[build_type]
        for allowable_type_name in curr_site_type.legal_terrain:
            if allowable_type_name == self.select_hex.hex_type.name:
                return True
        
        return False
    
    def set_selected(self, selected_unit):
        self.selected_unit = selected_unit
        
        if self.selected_unit == None:
            self.hide()
            return
    
        self.clear_children()
        
        if selected_unit != None and selected_unit.can_use_items():
            self.add_child(self.item_button)
            
        if self.can_build():
            self.add_child(self.build_button)
            self.build_button.set_label("Build [" + 
                                        str(misc_commands.get_build_cost(selected_unit.trait_value(trait.BUILD), 
                                                                         selected_unit.get_level())) + "]")
        
        if self.can_embassy():
            self.add_child(self.embassy_button)
            self.embassy_button.set_label("Embassy [" + 
                                        str(misc_commands.get_embassy_cost(self.selected_unit,
                                                                            self.select_hex.site.get_level())) + "]")
        
        x = self.rect.x + (self.rect.width / 4)
        y = self.rect.y + 4
        label_height = image.UI_ICON_HEIGHT 
        new_label = Label(Rect(x, y, self.rect.width / 2, label_height), self.selected_unit.get_name(), font=text.lg_font)
        self.add_child(new_label)
        y += (label_height * 2) / 3
          
        if self.selected_unit.has_trait(trait.HERO):
            level_text = ""
        else:
            level_text = "Lv. " + str(self.selected_unit.get_level())
        new_label = Label(Rect(x, y, self.rect.width / 2, label_height / 2), 
                         level_text  + " " + self.selected_unit.get_type_text(), font=text.sm_font)
        self.add_child(new_label)
        y += label_height / 3

        image_icons = [self.image_data.strength, self.image_data.armor, self.image_data.looting, self.image_data.health]
        text_labels = [str(self.selected_unit.get_strength()), str(self.selected_unit.get_armor()), str(self.selected_unit.get_looting()),  
                       str(self.selected_unit.get_health() - self.selected_unit.curr_wounds()) + "/" + str(self.selected_unit.get_health())]
        label_tooltips = ["Strength (better chance to win combats)", "Armor (better chance block hits)", "Looting (more gold and better loot)", "Health (num. wounds)"]                                                                                                     
        x = self.rect.x + self.rect.width / 6
        for i in range(len(image_icons)):
            new_label = Label(Rect(x, y, image.UI_ICON_WIDTH, image.UI_ICON_HEIGHT), 
                              image_icons[i], image_label=True)
            self.add_child(new_label)
            x += image.UI_ICON_WIDTH + 5
            new_label = Label(Rect(x, y, 10, image.UI_ICON_HEIGHT), 
                              text_labels[i], tool_tip_text=label_tooltips[i])
            self.add_child(new_label)
            x += 10
            if x > self.rect.x + self.rect.width - (image.UI_ICON_WIDTH + 15):
                x = self.rect.x + self.rect.width / 6
                y += image.UI_ICON_HEIGHT
        
        #y += image.UI_ICON_HEIGHT
        x += 10 #self.rect.x + self.rect.width / 6
        #TODO: other image for flight mode
        move_icon = self.image_data.naval_move if self.selected_unit.get_move_mode() == move_mode.NAVAL else self.image_data.foot_move
        new_label = Label(Rect(x, y, image.UI_ICON_WIDTH, image.UI_ICON_HEIGHT), move_icon, image_label=True)
        self.add_child(new_label)
        x += image.UI_ICON_WIDTH + 10
        new_label = Label(Rect(x, y, 15, image.UI_ICON_HEIGHT), 
                              str(self.selected_unit.get_moves_left()) + "/" + str(self.selected_unit.get_max_moves()), tool_tip_text="Move points left / Max move points")
        self.add_child(new_label)
        y += image.UI_ICON_HEIGHT
        
        traits = self.selected_unit.get_traits()
            
        x = self.rect.x + self.rect.width / 4
        width = self.rect.width / 2
        height = 12
        for curr_trait in traits:
            if curr_trait == trait.HERO:
                continue # no need to display this, already shown in unit type
            
            trait_text = trait.trait_str(curr_trait, traits[curr_trait])
            trait_label = Label(Rect(x, y, width, height), trait_text, tool_tip_text = trait.tool_tip_table[curr_trait])
            self.add_child(trait_label)
            
            if curr_trait in trait.useable_traits:
                use_callback = lambda used_trait = curr_trait: event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [misc_commands.UseTraitCommand(self.selected_unit, used_trait)]))
                use_button = Button(Rect(x + width + 2, y, 25, height), "Use", use_callback)
                self.add_child(use_button)
            y += 14    
        
        self.show()

    def render(self, surface, images):
        super(UnitRenderer, self).render(surface, images)
              