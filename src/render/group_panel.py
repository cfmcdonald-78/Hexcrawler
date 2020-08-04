'''
Created on Jul 2, 2012

@author: Chris
'''
import mob.unit as unit
import image
import hexcrawl.misc_commands as misc_commands
import mob.group as group, mob.trait as trait
from util.tools import Rect
from gui.button import Button
import gui.component as component
from core.event_manager import Event
import core.event_manager as event_manager
import text
from gui.label import Label

class UnitLabel(Label):
    
    def set_unit(self, curr_unit, index):
        self.curr_unit = curr_unit
        self.index = index
        self.overlays = []
        self.pending_overlays = []
    
    def render(self, surface, images):
        def draw_miniicon(miniicon, base_x, base_y, miniicon_pos):
            if miniicon_pos >= 9:
                return
            surface.blit(miniicon, (base_x + 4 + 16 * (miniicon_pos % 3), base_y + 3 + 16 * (miniicon_pos / 3)))
        
        miniicon_traits = {trait.SUPPLY: images.supply, trait.RESTRAINED: images.restrained_image, 
                           trait.EXHAUSTED: images.exhaustion, trait.INSPIRED: images.inspire, 
                           trait.BLOOD_POWER: images.blood}
        
        x, y = self.rect.x, self.rect.y
        
        unit_image = images.unit_image(self.curr_unit)
        slot_image = images.unit_slot
       
        surface.blit(slot_image, (x, y))
        surface.blit(unit_image, (x, y))
                #surface.blit(unit_image, (x, y))
        miniicon_pos = 0
        if not self.curr_unit.is_alive():
            surface.blit(images.dead_image, (x, y))
        elif self.curr_unit.is_wounded():
            wound_sixteenths = (self.curr_unit.curr_wounds() * 16) / self.curr_unit.get_health()
            for i in range(wound_sixteenths):
                surface.blit(images.wounded_image, (x, y + 58 - (i * 4)))
 
        for overlay_image in self.overlays:
                surface.blit(overlay_image, (x, y))
                
        if self.curr_unit.has_trait(trait.BURNING):
            surface.blit(images.burning_image, (x, y))
        for mini_trait in miniicon_traits:
            if self.curr_unit.has_trait(mini_trait):
                for j in range(self.curr_unit.trait_value(mini_trait)):
                    draw_miniicon(miniicon_traits[mini_trait], x, y, miniicon_pos)
                    miniicon_pos += 1
        
                    
    def add_overlay(self, image):
        self.pending_overlays.append(image)
        
    def swap_overlays(self):
        self.overlays = self.pending_overlays
        self.pending_overlays = []
    
#    # overlay an image on top of unit at index
#    def overlay(self, surface, image, index):
#        if index < 0 or index >= self.curr_group.num_units():
#            return
#        x, y = self.pixel_from_index(index)
#        surface.blit(image, (x, y))
        
    def event_handler(self, event):
        if event.type == component.MOUSE_CLICK:
            self.parent.mark_selected(self.index) # return unit_index # self.curr_group.get_unit(unit_index)
            return True
#        if event.type == component.MOUSE_DOWN or event.type == component.MOUSE_UP:
#            return True
        if event.type == component.KEY_DOWN:
            return self.parent.handle_key(event)  
        if event.type == component.MOUSE_DROP:
            return self.parent.handle_child_drop(event, self.index)
    
        return super(UnitLabel, self).event_handler(event)


class GroupRenderer(component.Component):
    '''
    classdocs
    '''

    def __init__(self, label, position_rect):
        super(GroupRenderer, self).__init__(position_rect)
        self.selected_index = None
        self.label = label
#        self.set_label(label, images)
        self.pending_overlays = {}
        self.overlays = {}
        
        self.curr_group = None
        self.curr_hex = None
        self.curr_mask = None
        self.curr_player = None
        self.pad = 4
        self.base_x = self.rect.x + 64
        self.unit_labels = []
        
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_SELECTED)
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_SHIFTED)
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_REMOVED)
        event_manager.add_listener(self.handle_game_events, event_manager.UNIT_ADDED)
    
    def set_label(self, label):
        self.label = label
    
    def set_data(self, curr_hex, curr_player, curr_mask):
        if curr_hex == None or curr_hex != self.curr_hex:
            self.selected_index = None
        self.curr_hex = curr_hex
        self.curr_player = curr_player
        self.curr_mask = curr_mask
       
    
    def handle_game_events(self, event):
        # only one unit in one group can be selected
        if event.type == event_manager.UNIT_SELECTED:
            if event.data['unit'] != None and self.curr_group != None and not self.curr_group.has_unit(event.data['unit']):
                self.selected_index = None
                #self.mark_selected(None)
     
        if event.type == event_manager.UNIT_ADDED:
            self.set_data(self.curr_hex, self.curr_player, self.curr_mask)
        elif event.type == event_manager.UNIT_REMOVED or event.type == event_manager.UNIT_SHIFTED:
            self.set_data(self.curr_hex, self.curr_player, self.curr_mask)
            
            if self.curr_group != None and self.curr_group == event.data['group']:
                if self.selected_index != None:
                    # re-select self in case selected unit has been disbanded
                    if self.selected_index >= self.curr_group.num_units():
                        self.mark_selected(self.curr_group.num_units() - 1)
                    else:
                        self.mark_selected(self.selected_index)
        
               
    def event_handler(self, event):
        if event.type == component.MOUSE_DROP:
            return self.handle_drop(event)
        return super(GroupRenderer, self).event_handler(event)
    
    def handle_key(self, event):
        return False
    
    def handle_drop(self, event):
        return False
    
    def handle_child_drop(self, event, index):
        return False
    
    def get_unit(self, index):
        return self.curr_group.get_unit(index)
    
    def index_from_pixel(self, x, y, y_min, y_max):
        if y < y_min or y > y_max:
            return -1
        
        index = (x - self.base_x) / (image.UNIT_WIDTH + self.pad)
        if x - self.base_x - index * (image.UNIT_WIDTH + self.pad) < image.UNIT_WIDTH:
            return index
        return -1
    
    def pixel_from_index(self, index):
        x = self.base_x + (self.pad + image.UNIT_WIDTH) * index
        y = self.rect.y + self.pad
        return x, y
            
    def has_group(self):
        return self.curr_group != None
    
    def set_group(self, curr_group):
        self.curr_group = curr_group
        if curr_group == None:
            self.clear_children()
            return
        
        self.update_units()
        
    def update_units(self):
        self.unit_labels = []
        self.clear_children()
        for i in range(self.curr_group.num_units()):
            x, y = self.pixel_from_index(i)
            unit_label = UnitLabel(Rect(x, y, image.UNIT_WIDTH, image.UNIT_HEIGHT), None, image_label = True)
            unit_label.set_unit(self.curr_group.get_unit(i), i)
            self.add_child(unit_label)
            self.unit_labels.append(unit_label)
        self.refresh_view()
    
    def mark_selected(self, index):
        self.selected_index = index  
        selected_unit = None if index == None else self.curr_group.get_unit(index)
        event_manager.queue_event(Event(event_manager.UNIT_SELECTED, [selected_unit]))
    
    def add_overlay(self, image, index):
        self.unit_labels[index].add_overlay(image)

    def swap_overlays(self):
        for unit_label in self.unit_labels:
            unit_label.swap_overlays()
          
    def render(self, surface, images, scale_selected=False):
       
        if not self.has_group():
            return 
            
        x = self.rect.x + self.pad * 6
        y = self.rect.y + self.pad * 3
            
        images.text.draw_text(self.label, text.sm_font, x, y, surface)
        region_pad = 4
#        images.draw_9patch(surface, images.region_9patch, Rect(self.rect.x + region_pad, 
#                                                               self.rect.y + region_pad, 
#                                                               self.rect.width - 2*region_pad, 
#                                                                self.rect.height - 2*region_pad))
        
        if self.selected_index != None:
            x, y = self.pixel_from_index(self.selected_index)
            surface.blit(images.selected_unit, (x, y))
    

class CombatRenderer(GroupRenderer):
    
    def render(self, surface, images):
        super(CombatRenderer, self).render(surface, images, True)
    
    def mark_selected(self, index):
        if index >= 0 and index < self.curr_group.num_units():
            self.selected_index = index  

    def selected_anchor_point(self, bottom):
        if self.selected_index == None or self.curr_group.get_unit(self.selected_index) == None:
            return None, None
        
        x, y = self.pixel_from_index(self.selected_index)
        x += image.UNIT_WIDTH / 2
        if bottom:
            y += image.UNIT_HEIGHT + 2
        else:
            y -= 2 
        return x, y

class OccupantRenderer(GroupRenderer):
    
    def __init__(self, label, position_rect, is_garrison):
        super(OccupantRenderer, self).__init__(label, position_rect)
        self.garrison = is_garrison
    
    def set_partner(self, partner):
        self.partner_renderer = partner
    
    def set_data(self, curr_hex, curr_player, curr_mask):
        super(OccupantRenderer, self).set_data(curr_hex, curr_player, curr_mask)
        if self.curr_hex != None:
            if self.garrison:
                new_group = self.curr_hex.get_garrison()
            else:
                new_group = self.curr_hex.get_active_group()
        else:
            new_group = None
            
        self.set_group(new_group)
        
    def update_units(self):
        super(OccupantRenderer, self).update_units()
        for i in range(self.curr_group.num_units()):
            if self.curr_group.get_owner() == self.curr_mask.get_player():
                self.unit_labels[i].set_draggable(True)
    
    def handle_key(self, event):
        key_val = event.unicode
        
        if self.selected_index == None or self.curr_group == None or self.curr_player != self.curr_group.get_owner():
            return False
        
        if key_val == 'x':
            command = misc_commands.UnitDisbandCommand(self.curr_group, self.selected_index)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True

        if '1' <= key_val <= '8':
            key_num = int(key_val)
            if key_num <= self.curr_group.num_units():
                command = misc_commands.UnitShiftCommand(self.curr_group, self.selected_index, key_num - 1)
                event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
                return True
    
        if key_val ==  't':
            to_garrison = not self.garrison
            command = misc_commands.UnitTransferCommand(self.curr_group.get_hex(), to_garrison, self.selected_index)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True
        
        return False
    
    def check_drop_transfer(self, dropped_icon):
        if dropped_icon in self.partner_renderer.unit_labels:
            # unit transfer
            orig_index = self.partner_renderer.unit_labels.index(dropped_icon)
            to_garrison = self.garrison
            command = misc_commands.UnitTransferCommand(self.partner_renderer.curr_group.get_hex(), to_garrison, orig_index)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True
        return False
    
    def handle_drop(self, event):
        return self.check_drop_transfer(event.dropped)
    
    def handle_child_drop(self, event, new_index):
        dropped_icon = event.dropped
        if dropped_icon in self.unit_labels:
            # unit shift
            orig_index = self.unit_labels.index(dropped_icon) 
            command = misc_commands.UnitShiftCommand(self.curr_group, orig_index, new_index)
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True
        if self.check_drop_transfer(dropped_icon):
            return True
       
        return False 
    
    def render(self, surface, images):            
        super(OccupantRenderer, self).render(surface, images)
        
        if not self.has_group():
            return
        
        x = self.base_x + image.UNIT_WIDTH / 2
        y = self.rect.y + self.rect.height + 6
        for i in range(self.curr_group.num_units()):
            images.text.draw_text(str(i + 1), text.sm_font, x, y, surface)
            x += image.UNIT_WIDTH + self.pad
     
class HireRenderer(GroupRenderer):
    
    
    def __init__(self, label, position_rect):
        super(HireRenderer, self).__init__(label, position_rect)
        self.curr_site = None

    def set_data(self, curr_hex, curr_player, curr_mask):
        super(HireRenderer, self).set_data(curr_hex, curr_player, curr_mask)
        self.curr_site = None if curr_hex == None else curr_hex.site
        self.set_group(None if self.curr_site == None else self.curr_site.get_units_for_hire())
        
    def update_units(self):
        super(HireRenderer, self).update_units()
        
        if self.curr_group == None:
            return
        
        hire_callbacks = [lambda i=x: self.do_hire(i) for x in range(self.curr_group.num_units())]
        self.hire_buttons = []
        
        for i in range(self.curr_group.num_units()):
            x, y = self.pixel_from_index(i)
            y += image.UNIT_HEIGHT + self.pad
            width, height = image.UNIT_WIDTH, image.UNIT_HEIGHT/ 3
            
            curr_unit = self.curr_group.get_unit(i)
            hire_cost = curr_unit.hire_cost(self.curr_hex.get_active_group())
            maint_cost = abs(curr_unit.maintenance())
            maint_label = "" if maint_cost == 0 else " / " + str(maint_cost)
            maint_tool_tip = "" if maint_cost == 0 else "\n and " + str(maint_cost) + " gold per week"
            
            label_text = str(hire_cost) + maint_label
            tool_tip =  "Hire this unit for " + str(hire_cost) + " gold" + maint_tool_tip
            
            self.hire_buttons.append(Button (Rect(x, y, width, height), label_text, hire_callbacks[i], tool_tip_text = tool_tip))
            self.add_child(self.hire_buttons[i])
        self.refresh_view()
        
    def do_hire(self, hire_index):
        self.curr_site.hire(self.curr_player, hire_index)
    