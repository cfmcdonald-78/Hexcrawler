'''
Created on Aug 6, 2012

@author: Chris
'''
from core.event_manager import Event
import core.event_manager as event_manager
from util.tools import Rect
import component
import render.text as text
from component import Component

class Button(Component):
    # set image_label true if the label is an image rather than text
    def __init__(self, position_rect, label, on_click, font=None, image_label=False, tool_tip_text = None):
        super(Button, self).__init__(position_rect, tool_tip_text=tool_tip_text)
        self.label = label
        self.image_label = image_label
        self.down = False
        self.on_click = on_click
        self.label_font = font
        
    def set_label(self, label, image_label=False):
        self.label = label
        self.image_label = image_label
        
    def set_tool_tip(self, tool_tip_text):
        self.tool_tip_text = tool_tip_text
        
    # no reason for button to have focus atm
    def takes_focus(self):
        return False
        
    def event_handler(self, event):
        if event.type == component.MOUSE_DOWN:
            self.down = True
            return True
        elif event.type == component.MOUSE_UP:
            self.down = False
            return True
        elif event.type == component.MOUSE_CLICK:
            event_manager.queue_event(Event(event_manager.BUTTON_CLICK, [self, self.down]))
            if self.on_click != None:
                self.on_click()
            return True
        return super(Button, self).event_handler(event)
    
    def is_down(self):
        return self.down    
    
#    def ee(self, event):
#        if event.type == event_manager.BUTTON_DOWN_DONE and event.data['button'] == self:
#            self.down = False
#    
#    def handle_mouse(self, x, y):
#        event_manager.queue_event(Event(event_manager.BUTTON_CHANGE, [self, self.down]))
#        self.down = True
#        process_manager.attach_process(DelayedEventProcess(BUTTON_DOWN_TIME, Event(event_manager.BUTTON_DOWN_DONE, [self])))
#        
#        if self.callback != None:
#            return self.callback()
       
    def render(self, surface, images):
        images.draw_button(surface, self.rect, self.down)
        
        if self.image_label:
            surface.blit(self.label, (self.rect.x, self.rect.y))
        else:
            draw_font = text.sm_font if self.label_font == None else self.label_font
            images.text.draw_text(self.label, draw_font, self.rect.x + self.rect.width / 2,
                                  self.rect.y + self.rect.height / 2, surface, color = text.LIGHT)

HORIZONTAL = 0
VERTICAL = 1

class Toggle(Button):
    
    def __init__(self, position_rect, label, on_toggle, image_label=False,  down=False):
        super(Toggle, self).__init__(position_rect, label, None, image_label)
        self.on_toggle = on_toggle
        self.down = down
    
    def event_handler(self, event):
        if event.type == component.MOUSE_DOWN:
            event_manager.queue_event(Event(event_manager.BUTTON_CLICK, [self, self.down]))
            self.toggle()
            if self.on_toggle != None:
                self.on_toggle(self.down)
        
        if event.type in component.mouse_events:
            return True
        
        return False
        
#        elif event.type == component.MOUSE_UP:
#            self.down = False
#        elif event.type == component.MOUSE_CLICK:
#            self.on_click()
    
#    def handle_mouse(self, x, y):
#        event_manager.queue_event(Event(event_manager.BUTTON_CHANGE, [self, self.down]))
#        self.toggle()
#        
#        if self.callback != None:
#            return self.callback()
    def set(self, down):
        self.down = down
    
    def reset(self):
        self.down = False
    
    def toggle(self):
        self.down = not self.down
    
    def render(self, surface, images):
        images.draw_button(surface, self.rect, self.down)
        
        if self.image_label:
            surface.blit(self.label, (self.rect.x, self.rect.y))
        else:
            images.text.draw_text(self.label, text.sm_font, self.rect.x + self.rect.width / 2,
                                  self.rect.y + self.rect.height / 2, surface, color=text.LIGHT)

class ToggleGroup(Component):
    
    def __init__(self, position_rect, button_labels, callback, orient=HORIZONTAL, default_index=0):
        super(ToggleGroup, self).__init__(position_rect)
        pad = 4
        
        num_buttons = len(button_labels)
        assert(num_buttons > 1)
        
        # compute button positions
        if orient == VERTICAL:
            width = self.rect.width - 2 * pad
            height = (self.rect.height - (2 + num_buttons - 1) * pad) / num_buttons  
        else:
            width = (self.rect.width - (2 + num_buttons - 1) * pad) / num_buttons  
            height = self.rect.height - 2 * pad  
        
       
        self.toggles = []
        for i in range(num_buttons):
            x = self.rect.x + pad if orient == VERTICAL else self.rect.x + (i + 1) * pad + i * width
            y = self.rect.y + pad if orient == HORIZONTAL else self.rect.y + (i + 1) * pad + i * height
            new_toggle = Toggle( Rect(x, y, width, height), button_labels[i], None)
            new_toggle.suppress()
            self.toggles.append(new_toggle)
            self.add_child(new_toggle)
          
        self.down_index = default_index
        self.toggles[self.down_index].toggle()
        self.callback = callback
    
    def event_handler(self, event):
        # determine which toggle, if any was selected
        if event.type == component.MOUSE_DOWN:
            x, y = event.pos
            pushed_index = self.index_from_pixel(x, y)
            if pushed_index == None:
                return True
        
            # if toggle down, do nothing
            if pushed_index == self.down_index:
                return True
     
            # switch down toggle
            self.toggles[self.down_index].toggle()
            self.down_index = pushed_index
            self.toggles[self.down_index].toggle()
            
            self.callback(self.down_index)
            event_manager.queue_event(Event(event_manager.BUTTON_CLICK, [self.toggles[self.down_index]]))
            return True
        
        return super(ToggleGroup, self).event_handler(event)
    
    def index_from_pixel(self, x, y):
        for i in range(len(self.toggles)):
            if self.toggles[i].contains(x, y):
                return i
        return None
        
    
    