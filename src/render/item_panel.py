'''
Created on Nov 4, 2012

@author: Chris
'''
import image, text
from gui.modal import ModalDialog
from gui.button import Button
from gui.label import Label
import gui.component as component
import mob.hero as hero
import mob.trait as trait
from util.tools import Rect
import core.event_manager as event_manager
from core.event_manager import Event
import hexcrawl.misc_commands as misc_commands

EQUIP_SLOT = 0
PACK_SLOT = 1

class ItemLabel(Label):
    
    def __init__(self, position_rect, base_icon, index):
        super(ItemLabel, self).__init__(position_rect, base_icon, image_label=True)
        self.curr_item = None
        self.index = index
        self.selected = False
        
    def set_item(self, new_item):
        self.curr_item = new_item
        self.draggable = self.curr_item != None
    
    def render(self, surface, images):
        super(ItemLabel, self).render(surface, images)
        
        if self.curr_item != None:
            surface.blit(images.item_icons[self.curr_item.get_icon()], (self.rect.x, self.rect.y))
            
        if self.selected:
            surface.blit(images.selected_item, (self.rect.x, self.rect.y)) 
    
    def mark_selected(self, selected):
        self.selected = selected
    
    def event_handler(self, event):
        if event.type == component.MOUSE_CLICK:
            self.mark_selected(True)
            self.parent.mark_selected(self.index) # return unit_index # self.curr_group.get_unit(unit_index)
            return True
        if event.type == component.KEY_DOWN:
            return self.parent.handle_key(event)  
        if event.type == component.MOUSE_DROP:
           return self.parent.handle_child_drop(event, self.index)
        return super(ItemLabel, self).event_handler(event)

class ItemDialog(ModalDialog):
    
    def __init__(self, width, height, head_text, item_unit, can_sell_items, images):
        super(ItemDialog, self).__init__(width, height, head_text)
        self.unit = item_unit
        self.selected_item = None
        self.pad = (width - (image.ITEM_ICON_WIDTH + 4) * len(hero.EQUIP_SLOTS)) / 2
        self.trait_labels = []
        
        def transfer_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 't', key = 't')
        
        x = self.rect.x + (self.rect.width - (image.SM_BUTTON_WIDTH * 2 + 8) - 50) / 2
        y = self.rect.y + image.ITEM_ICON_HEIGHT * 2 + 4
        self.transfer_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.transfer,  
                                      transfer_callback,  image_label = True,  tool_tip_text = "transfer (t)")
        x += image.SM_BUTTON_WIDTH + 4
        
        def disband_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 'x', key = 'x')
        
        #self.refresh_buttons()
        
        self.disband_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.disband,  
                                     disband_callback, image_label = True,  tool_tip_text = "discard (x)")
        self.add_child(self.transfer_button)
        self.add_child(self.disband_button)
        
        def sell_callback():
            self.sell_selected()
        
        if can_sell_items:
#            width = 50
#            height = 25
            x += image.SM_BUTTON_WIDTH + 4
#            y = self.rect.y + image.ITEM_ICON_HEIGHT * 2 - height/2
            self.add_child(Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), 
                                  images.gold_small, sell_callback, image_label = True, 
                                  tool_tip_text = "sell (s)"))
        
        x, y = self.rect.x + self.pad, self.rect.y + image.ITEM_ICON_HEIGHT
        self.item_icons = []
        for i in range(len(hero.EQUIP_SLOTS)):
            item_icon = ItemLabel(Rect(x,y,image.ITEM_ICON_WIDTH, image.ITEM_ICON_HEIGHT), 
                                      images.equip_slots[hero.EQUIP_SLOTS[i]], (EQUIP_SLOT, i))
            self.add_child(item_icon)
            self.item_icons.append(item_icon)
            x += image.ITEM_ICON_WIDTH + 4
            
        y += image.ITEM_ICON_HEIGHT + 8 + image.SM_BUTTON_HEIGHT
        x = self.rect.x + self.pad
        for i in range(hero.BACKPACK_SIZE):
            item_icon = ItemLabel(Rect(x,y,image.ITEM_ICON_WIDTH, image.ITEM_ICON_HEIGHT), 
                                  images.backpack_slot, (PACK_SLOT, i))
            self.add_child(item_icon)
            self.item_icons.append(item_icon)
            x += image.ITEM_ICON_WIDTH + 4
        
        self.refresh_items()
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_ADDED)
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_SHIFTED)
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_REMOVED)
    
    def handle_game_events(self, event):
        self.refresh_items()
        self.mark_selected(None)
    
    def refresh_items(self):
        for i in range(len(hero.EQUIP_SLOTS)):
            self.item_icons[i].set_item(self.unit.get_equipped_item(i))
        
        for i in range(hero.BACKPACK_SIZE):
            self.item_icons[len(hero.EQUIP_SLOTS) + i].set_item(self.unit.get_backpack_item(i))
          
    def sell_selected(self):
        if self.selected_item == None:
            return
        command =  misc_commands.ItemSellCommand(self.unit, self.selected_item[0] == PACK_SLOT, self.selected_item[1])
        event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
    
    def event_handler(self, event):
        if event.type == component.KEY_DOWN:
            key_val = event.unicode
            # equip/unequip/destroy selected item
            if key_val == 't' and self.selected_item != None:
                # equip/unequip selected item
                command =  misc_commands.ItemTransferCommand(self.unit, self.selected_item[0] == PACK_SLOT, self.selected_item[1])
                event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
                return True
            if key_val == 'x' and self.selected_item != None:
                # throw away selected item
                command =  misc_commands.ItemDiscardCommand(self.unit, self.selected_item[0] == PACK_SLOT, self.selected_item[1])
                event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
                return True
            if key_val == 's' and self.selected_item != None:
                # sell selected item
                self.sell_selected()
                return True
        
        return super(ItemDialog, self).event_handler(event)
    
    def handle_child_drop(self, event, new_index):
        dropped_icon = event.dropped
        if dropped_icon.index[0] != new_index[0]:
            command =  misc_commands.ItemTransferCommand(self.unit, dropped_icon.index[0] == PACK_SLOT, dropped_icon.index[1])
            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            # unit shift
#            orig_index = self.unit_labels.index(dropped_icon) 
#            command = misc_commands.UnitShiftCommand(self.curr_group, orig_index, new_index)
#            event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True
#        if self.check_drop_transfer(dropped_icon):
#            return True
       
        return False 
    
    def mark_selected(self, index):
        if self.selected_item != None and self.selected_item != index:
            # deselect previous selection
            self.item_icons[self.selected_item[0] * len(hero.EQUIP_SLOTS) + self.selected_item[1]].mark_selected(False)
        self.selected_item  = index
        
        # clear old trait labels
        for trait_label in self.trait_labels:
            self.remove_child(trait_label)
        self.trait_labels = []
        
        if index == None:
            return
    
        row, column = self.selected_item
        selected_item = self.unit.get_equipped_item(column) if row == EQUIP_SLOT else self.unit.get_backpack_item(column)
        if selected_item == None:
            return
    
        x = self.rect.x + self.rect.width / 4
        y = self.rect.y + image.SM_BUTTON_HEIGHT + (3 * image.ITEM_ICON_HEIGHT) + 20    
        name_label = Label(Rect(x, y, self.rect.width/2, 20), selected_item.get_name(), font = text.lg_font)
        self.trait_labels.append(name_label)    
        self.add_child(name_label)
        #images.text.draw_text(selected_item.get_name(), text.lg_font, x, y, surface)
    
        # create new trait labels
     #   x = self.rect.x + 30
        x_vals = [self.rect.x + (self.rect.width / 5), 
                      self.rect.x + ((self.rect.width * 11) / 20)]
      
        traits = selected_item.get_traits()
        x_index = 0
        y += 18;
        for curr_trait in traits:
            trait_text = curr_trait
            if not isinstance(traits[curr_trait], bool):
                trait_text += " " + str(traits[curr_trait])
            trait_label = Label(Rect(x_vals[x_index], y, self.rect.width/4, 12), trait_text, tool_tip_text = trait.tool_tip_table[curr_trait])
            self.add_child(trait_label)
            self.trait_labels.append(trait_label)
            
            x_index = (x_index + 1) % len(x_vals)
            if x_index == 0:
                y += 14
        self.show()
    
    def index_from_pixel(self, x, y, y_min, y_max):
        if y < y_min or y > y_max:
            return -1
        base_x = self.rect.x + self.pad
        index = (x - base_x) / (image.ITEM_ICON_WIDTH + 8)
        if x - base_x - index * (image.ITEM_ICON_WIDTH + 8) < image.ITEM_ICON_WIDTH:
            return index
        return -1
    
    def render(self, surface, images):
        super(ItemDialog, self).render(surface, images)
        
#            
        ## render item information if there's a selected item
       # if self.selected_item != None:
         
           
            #images.text.draw_text(self.selected_item.get_gold_value(), text.sm_font, x + )
            #y += 16
           
         
      
    