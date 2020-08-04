'''
Created on Jul 20, 2012

@author: Chris
'''
import core.event_manager as event_manager
import pygame
from core.event_manager import Event
import core.options as options
from util.tools import Rect, inside
from button import Button, Toggle, ToggleGroup
from label import Label
import render.image as image
import render.text as text
#import mob.unit as unit
import mob.hero as hero
import hexcrawl.misc_commands as misc_commands
import component
from component import Component

OK_BUTTON_WIDTH = 60
OK_BUTTON_HEIGHT = 30

class ModalDialog(component.Window):
    '''
    classdocs
    '''


    def __init__(self, width, height, head_text):
#        x, y = Component.get_modal_position()
        super(ModalDialog, self).__init__(Rect(0, 0, width, height), True)
        self.head_text = head_text
        
        def close_callback():
            self.close_window()
        self.add_child ( Button(Rect(self.rect.x + ((self.rect.width - OK_BUTTON_WIDTH) / 2), 
                                     self.rect.y + self.rect.height - OK_BUTTON_HEIGHT - 8,
                                 OK_BUTTON_WIDTH, OK_BUTTON_HEIGHT), "Close", close_callback))
    
#    def open_window(self):
#        event_manager.trigger_event(Event(event_manager.MODAL_DIALOG, [self, True]))
#    
#    def close_window(self):
#        self.
#        event_manager.trigger_event(Event(event_manager.MODAL_DIALOG, [self, False]))

    def close_window(self):
        self.hide()
        
    def event_handler(self, event):
        if event.type == component.KEY_DOWN:
            if event.key == component.K_ESC:
                self.close_window()
                return True
        
        return super(ModalDialog, self).event_handler(event)
    
    def render(self, surface, images):
        super(ModalDialog, self).render(surface, images)
#        surface.fill ((0, 127, 127), self.rect)
#        images.draw_window(surface, self.rect)
        
        images.text.draw_text(self.head_text, text.vlg_font, self.rect.x + self.rect.width / 2,
                                self.rect.y + 16, surface)
        
#        self.close_button.render(surface, images)
#        surface.fill ((160, 82, 45), self.close_button)
#        images.text.draw_text("Close", images.text.lg_font, self.close_button.x + self.close_button.width /2 ,
#                                  self.close_button.y + self.close_button.height /2, surface)

class TextDialog(ModalDialog):
    
    def __init__(self, head_text, body_text):
        self.body_text = body_text
        self.body_font = text.lg_font
        
        text_width, text_height = text.block_size(self.body_text, self.body_font)
        win_width = int(text_width * 1.5)
        win_height = int(text_height * 1.5) + text.vlg_font.get_height() + OK_BUTTON_HEIGHT + 24
        
        super(TextDialog, self).__init__(win_width, win_height, head_text)
        
        self.body_x =  self.rect.x + (self.rect.width - text_width) / 2
        self.body_y = self.rect.y + text.vlg_font.get_height() + 16
        
    def render(self, surface, images):
        super(TextDialog, self).render(surface, images)
    
        images.text.draw_text_block(self.body_text, self.body_font, self.body_x, self.body_y, surface)
    
#class ChoiceDialog(TextDialog):
#    
#    def __init__(self, head_text, body_text, choices):
#        super(ChoiceDialog, self).__init__(head_text, body_text)
#        
#        # delete OK button created by ModalDialog 
#        self.clear_children()
#        
#        # create buttons for choices
#        num_buttons = len(choices)
#        x = self.rect.x + 
#        for i in range(num_buttons): 
#            event, event_data = choices[i]
#            button_callback = lambda x=event, y=event_data: event_manager.queue_event(Event(x, y))
#            self.add_child(Button(Rect(self.rect.x + ((self.rect.width - OK_BUTTON_WIDTH) / 2), 
#                                     self.rect.y + self.rect.height - OK_BUTTON_HEIGHT - 8,
#                                 OK_BUTTON_WIDTH, OK_BUTTON_HEIGHT), "Close", close_callback))
#        def close_callback():
#            self.close_window()
#            self.add_child ( Button(Rect(self.rect.x + ((self.rect.width - OK_BUTTON_WIDTH) / 2), 
#                                     self.rect.y + self.rect.height - OK_BUTTON_HEIGHT - 8,
#                                 OK_BUTTON_WIDTH, OK_BUTTON_HEIGHT), "Close", close_callback))
#         
#    
    

class ToolsDialog(ModalDialog):
    
    def __init__(self, width, height, head_text):
        super(ToolsDialog, self).__init__(width, height, head_text)
        
        pad = 16
        width, height  = self.rect.width / 3, self.rect.height / 8
        x, y = self.rect.x + self.rect.width /2 - width/2, self.rect.y + 3*pad
        
        def save_callback():
            event_manager.queue_event(Event(event_manager.QUIT, [True]))
        
        self.add_child(Button(Rect(x, y, width, height), "Save and Quit", save_callback))
#        y += self.rect.height / 8 + pad
#        self.add_child(Button(Rect(x, y, width, height), "Load", None))
#        
        def sound_callback(is_down):
            options.curr_options.sound = is_down
            event_manager.queue_event(Event(event_manager.SOUND_CHANGE, [is_down]))
        
        y += self.rect.height / 8 + pad
        self.add_child(Toggle(Rect(x, y, width, height), "Sound", sound_callback, down= options.curr_options.sound))
        
        def music_callback(is_down):
            options.curr_options.music = is_down
            event_manager.queue_event(Event(event_manager.MUSIC_CHANGE, [is_down]))
        
        y += self.rect.height / 8 + pad
        self.add_child(Toggle(Rect(x, y, width, height), "Music", music_callback, down= options.curr_options.music))
        
        def own_combat_speed_callback(position):
            options.curr_options.own_combat_speed = position
            event_manager.queue_event(Event(event_manager.COMBAT_SPEED_CHANGE, [True, position]))
            
            
        y += height + pad
        x = self.rect.x + (self.rect.width - width * 2) / 2
        self.add_child(Label(Rect(x, y + 8, 50, 16), "Combat:"))
        x += 50
       
        self.add_child(ToggleGroup(Rect(x, y, width * 2 - 50, height), ["Slow", "Med.","Fast"], own_combat_speed_callback, 
                                   default_index = options.curr_options.own_combat_speed))
        
         
    
class GameOverDialog(ModalDialog):
    
    def __init__(self, width, height, head_text, body_text):
        super(GameOverDialog, self).__init__(width, height, head_text)
        self.body_text = body_text
        self.head_text = head_text
        
    def close_window(self):
        super(GameOverDialog, self).close_window()
        event_manager.trigger_event(Event(event_manager.QUIT, [False]))
        
    def render(self, surface, images):
        super(GameOverDialog, self).render(surface, images)
    
        images.text.draw_text(self.body_text, text.lg_font, self.rect.x + self.rect.width / 2 ,
                                  self.rect.y + self.rect.height /2, surface)


    