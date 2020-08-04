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

PACK_SLOT = 0
EQUIP_SLOT = 1

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
        self.trait_labels = []
        
        # backpack slots
        self.item_icons = []
        y = self.rect.y + 32 
        x = self.rect.x + 32
        for i in range(hero.BACKPACK_SIZE):
            item_icon = ItemLabel(Rect(x,y,image.ITEM_ICON_WIDTH, image.ITEM_ICON_HEIGHT), 
                                  images.backpack_slot, (PACK_SLOT, i))
            self.add_child(item_icon)
            self.item_icons.append(item_icon)
            y += image.ITEM_ICON_HEIGHT + 4
        x += image.ITEM_ICON_WIDTH + 16
        
        # equip slots
        y = self.rect.y + 32
        for i in range(len(hero.EQUIP_SLOTS)):
            item_icon = ItemLabel(Rect(x,y,image.ITEM_ICON_WIDTH, image.ITEM_ICON_HEIGHT), 
                                      images.equip_slots[hero.EQUIP_SLOTS[i]], (EQUIP_SLOT, i))
            self.add_child(item_icon)
            self.item_icons.append(item_icon)
            y += image.ITEM_ICON_HEIGHT + 4
        x += image.ITEM_ICON_WIDTH + 4
        
        # buttons
        x = self.rect.x + 44
        def transfer_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 't', key = 't')
        self.transfer_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.transfer,  
                                      transfer_callback,  image_label = True,  tool_tip_text = "transfer (t)")
        x += image.SM_BUTTON_WIDTH + 4
        
        def disband_callback():
            component.post_ui_event(component.KEY_DOWN, unicode = 'x', key = 'x')
        self.disband_button = Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), images.disband,  
                                     disband_callback, image_label = True,  tool_tip_text = "discard (x)")
        self.add_child(self.transfer_button)
        self.add_child(self.disband_button)
        x += image.SM_BUTTON_WIDTH + 4
        
        if can_sell_items:
            def sell_callback():
                self.sell_selected()
           
            self.add_child(Button(Rect(x, y, image.SM_BUTTON_WIDTH, image.SM_BUTTON_HEIGHT), 
                                  images.gold_small, sell_callback, image_label = True, 
                                  tool_tip_text = "sell (s)"))
        x += image.SM_BUTTON_WIDTH + 4
        
        self.refresh_items()
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_ADDED)
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_SHIFTED)
        event_manager.add_listener(self.handle_game_events, event_manager.ITEM_REMOVED)
    
    def handle_game_events(self, event):
        self.refresh_items()
        self.mark_selected(None)
    
    def refresh_items(self):
        for i in range(hero.BACKPACK_SIZE):
            self.item_icons[i].set_item(self.unit.get_backpack_item(i))
            
        for i in range(len(hero.EQUIP_SLOTS)):
            self.item_icons[hero.BACKPACK_SIZE + i].set_item(self.unit.get_equipped_item(i))
        
          
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
            return True
        
        return False 
    
    def mark_selected(self, index):
        if self.selected_item != None and self.selected_item != index:
            # deselect previous selection
            self.item_icons[self.selected_item[0] * hero.BACKPACK_SIZE + self.selected_item[1]].mark_selected(False)
        self.selected_item  = index
        
        # clear old trait labels
        for trait_label in self.trait_labels:
            self.remove_child(trait_label)
        self.trait_labels = []
        
        if index == None:
            return
    
        column, row = self.selected_item
        selected_item = self.unit.get_equipped_item(row) if column == EQUIP_SLOT else self.unit.get_backpack_item(row)
        if selected_item == None:
            return
    
        x = self.rect.x + 32 + image.ITEM_ICON_WIDTH * 2 + 20
        y = self.rect.y + 32    
        name_label = Label(Rect(x, y, self.rect.width/2, 20), selected_item.get_name()) #,font = text.lg_font)
        self.trait_labels.append(name_label)    
        self.add_child(name_label)
      
        traits = selected_item.get_traits()
        #x_index = 0
        y += 18
        value_label = Label(Rect(x, y, self.rect.width/2, 12), "Value: " + str(selected_item.get_gold_value()))
        self.trait_labels.append(value_label)    
        self.add_child(value_label)
        y += 18
        
        for curr_trait in traits:
            trait_text = trait.trait_str(curr_trait, traits[curr_trait])
            trait_label = Label(Rect(x, y, self.rect.width/2, 12), trait_text, tool_tip_text = trait.tool_tip_table[curr_trait])
            self.add_child(trait_label)
            self.trait_labels.append(trait_label)
            y += 14
            
        self.show()
    
    def render(self, surface, images):
        super(ItemDialog, self).render(surface, images)
        