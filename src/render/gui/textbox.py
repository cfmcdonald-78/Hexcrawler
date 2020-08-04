'''
Created on Aug 6, 2012

@author: Chris
'''
from util.tools import Rect
import component
from component import Component


class TextBox(Component):
#    focus = None
    
#    @classmethod
#    def set_focus(cls, text_box_instance):
#        cls.focus = text_box_instance
#        
#    @classmethod
#    def get_focus(cls):
#        return cls.focus
    
    def __init__(self, position_rect, max_chars, callback, default_text=""):
        self.text = default_text
        self.max_chars = max_chars
        
        # center textbox within desired space
        text_width, text_height = min(max_chars * 10, position_rect.width), 20
        x = position_rect.x + (position_rect.width/2 - text_width/2)
        y = position_rect.y + (position_rect.height/2 - text_height/2)
        new_rect = Rect(x, y, max_chars * 10, 20)
        
        super(TextBox, self).__init__(new_rect)
        self.callback = callback
        
    
    def get_text(self):
        return self.text
    
    def event_handler(self, event):
        if event.type == component.KEY_DOWN:

            keycode = event.unicode 
        
            if keycode == '\b' and len(self.text) > 0:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_chars and ((keycode >= 'A' and keycode <= 'z') or (keycode >= '0' and keycode <= '9') or keycode == ' '):
                self.text += keycode
            if self.callback != None:
                self.callback(self.text)
            return True
        
        return super(TextBox, self).event_handler(event)
    
    def render(self, surface, images):
        images.draw_textbox(surface, self.rect, self.text, self.has_focus())
    
    