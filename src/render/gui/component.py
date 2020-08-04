'''
Created on Aug 7, 2012

@author: Chris
'''
from util.tools import inside, Rect
import pygame
import render.text as text
import math

KEY_DOWN = pygame.KEYDOWN
KEY_UP = pygame.KEYUP
MOUSE_DOWN = pygame.MOUSEBUTTONDOWN
MOUSE_UP = pygame.MOUSEBUTTONUP
MOUSE_MOTION = pygame.MOUSEMOTION
TICK = pygame.USEREVENT
MOUSE_CLICK = pygame.USEREVENT + 1
MOUSE_HOVER = pygame.USEREVENT + 2
MOUSE_DRAG = pygame.USEREVENT + 3
MOUSE_DROP = pygame.USEREVENT + 4

MUSIC_DONE = pygame.USEREVENT + 5
AUTOSAVE = pygame.USEREVENT + 6

AUTOSAVE_INTERVAL = 300000

HOVER_TRIGGER_TICKS = 20

key_events = [KEY_DOWN, KEY_UP]
mouse_events = [MOUSE_DOWN, MOUSE_UP, MOUSE_MOTION, MOUSE_CLICK, MOUSE_HOVER, MOUSE_DRAG, MOUSE_DROP]

LEFT_MOUSE = 1
RIGHT_MOUSE = 3
K_ESC = pygame.K_ESCAPE
K_UP = pygame.K_UP
K_DOWN = pygame.K_DOWN
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT

def post_ui_event(event_type, **data):
    pygame.event.post(pygame.event.Event(event_type, data))

class Component(object):
    '''
    classdocs
    '''
    focus = None
    last_mouse_down = None
    modal_stack = []
    hover_component = None
    hover_tick_count = 0 
    tool_tip_text = None
    tool_tip_loc = None
    dragging = None
    
    @classmethod
    def set_top_level(cls, top_level_component, width, height, modal_center_x = None, modal_center_y = None):
        cls.modal_center_x = width/2 if modal_center_x == None else modal_center_x
        cls.modal_center_y = height/2  if modal_center_y == None else modal_center_y
        cls.window_width = width
        cls.window_height = height
        cls.top_level_component = top_level_component
        
    @classmethod
    def render_tooltip(cls, surface, images):
        ttip_font = text.sm_font
        ttip_width, ttip_height = text.block_size(cls.tool_tip_text, ttip_font)
        pad = 2
        
        ttip_width += pad*2
        ttip_height += pad*2
        x, y = cls.tool_tip_loc 
        
        # tool_tip_loc is position of the mouse, adjust box so that tooltip appears just above it
        x -= ttip_width/2
        y -=  ttip_height
        
        # final position adjustment to make sure tooltip will fit on screen
        if x < 0:
            x = 0
        if x + ttip_width >= cls.window_width:
            x = cls.window_width - ttip_width 
        if y < 0:
            y = 0
        if y + ttip_height >= cls.window_height:
            y = cls.window_height - ttip_height 
        
        surface.fill((200,220,200), (x, y, ttip_width, ttip_height))
        images.text.draw_text_block(cls.tool_tip_text, ttip_font, x + pad, y + pad, surface)

    def __init__(self, position_rect, modal=False, tool_tip_text = None, draggable = False):
        '''
        Constructor
        '''
        self.draggable = False
        
        if modal:
            # reposition modal according to desired centering
            self.rect = Rect(Component.modal_center_x - position_rect.width / 2, Component.modal_center_y - position_rect.height / 2,
                             position_rect.width, position_rect.height)
        else:
            self.rect = position_rect
#             get_modal_position(cls):
#        return cls.modal_x, cls.modal_y
        
        self.children = []
        self.shown = False
        self.modal = modal
        self.parent = None
        self.surrender_events = False
        self.tool_tip_text = tool_tip_text
        self.enabled = True
#        self.tool_tip_enabled = False
    
    def has_focus(self):
        return Component.focus == self
    
    def takes_focus(self):
        return True 
    
    def get_parent(self):
        return self.parent
    
    # force component to surrender event handling to its parent
    def suppress(self):
        self.surrender_events = True
    
    # child order = layering, will draw earlier children first and send them events last, so 'bottom' layer should be added first
    def add_child(self, new_child):
        assert(isinstance(new_child, Component))
        new_child.parent = self
        if new_child not in self.children:
            self.children.append(new_child)
        
    def remove_child(self, old_child):
        self.children.remove(old_child)
        
    def clear_children(self):
        self.children = []
        
    def event_handler(self, event):
        if event.type == MOUSE_HOVER and self.tool_tip_text != None:
            Component.set_tooltip(self.tool_tip_text, event.pos) #(self.rect.x + self.rect.width / 2, self.rect.y + self.rect.height/2))
        elif event.type == MOUSE_MOTION:
            Component.tool_tip_text = None
        # by default mouse events are absorbed, other events aren't
        elif event.type in mouse_events:
            return True
        else:
            return False
#   
    @classmethod 
    def has_active_modal(cls):
        return len(cls.modal_stack) > 0
    
    @classmethod
    def set_tooltip(cls, text, loc):
        cls.tool_tip_text = text
        cls.tool_tip_loc = loc
    
    @classmethod
    def has_active_tooltip(cls):
        return cls.tool_tip_text != None
    
    @classmethod
    def top_modal(cls):
        return cls.modal_stack[-1]
    
    @classmethod
    def clear_modals(cls):
        cls.modal_stack = []
    
    def contains(self, x, y):
        return inside(self.rect, x, y)
    
    # if show-all set to false, only show this component, don't
    # descend recursively through children
    def show(self, show_all=True):
        self.shown = True
        
        if show_all:
            for child in self.children:
                child.show()
                
        if self.modal and self not in Component.modal_stack:
            Component.modal_stack.append(self)

    def refresh_view(self):
        # if self is shown, make sure all children are shown
        if self.is_shown():
            self.show()
    
    def is_shown(self):
        return self.shown 
    
    def is_draggable(self):
        return self.draggable 
    
    def set_draggable(self, draggable):
        self.draggable = draggable
        
    def hide(self):
        self.shown = False
        for child in self.children:
            child.hide()
        if self.modal:
            Component.modal_stack.remove(self)
    
    def top_level(self):
        return self == Component.top_level_component
    
    # return true if event consumed, false otherwise
    def on_ui_event(self, event):
        if not self.shown or not self.enabled:
            return False
        
#        print "handling events on " + str(self)
        
         # if there's a modal window open, route all mouse and key events to the top one
        if Component.has_active_modal() and self.top_level() and (event.type in mouse_events or event.type in key_events):
            return Component.top_modal().on_ui_event(event)
        
        # if mouse event occurred inside a child component, have it handle the event
        if event.type in mouse_events:
            x, y = event.pos
            for child in reversed(self.children):
                if child.contains(x, y):
                    handled = child.on_ui_event(event)
                    if handled:
                        return True
            
        
        # send key events to whoever has focus.
        # If focused component doesn't handle it, handle it at top level.
        if self.top_level() and event.type in key_events:
            if Component.focus != None and Component.focus != self:
                handled = Component.focus.on_ui_event(event)
                if handled:
                    return True
            return self.event_handler(event)
        
        # always let parent handle events
        if self.surrender_events:
            return False
        
      
        if event.type == MOUSE_MOTION:
            motion_dist = math.hypot(event.rel[0], event.rel[1])
#            print motion_dist
            if Component.last_mouse_down != None and Component.last_mouse_down.is_draggable() and motion_dist >= 2:
                # trigger drag if mouse moved significant distance while buttton held down
                Component.dragging = (x, y)
                pygame.event.post(pygame.event.Event(MOUSE_DRAG, dragged=Component.last_mouse_down, pos = (x, y)))
            elif self != Component.hover_component:
                Component.hover_component = self
                Component.hover_loc = event.pos
                Component.hover_tick_count = 0 
            
                
        if event.type == TICK:
            # generate hover event if mouse stays over one component for a while
            Component.hover_tick_count += 1
            if Component.hover_tick_count == HOVER_TRIGGER_TICKS:
                pygame.event.post(pygame.event.Event(MOUSE_HOVER, pos = Component.hover_loc))
        
        # if mouse up happens on same component as last mouse down, send a click event
        if event.type == MOUSE_DOWN:
            Component.last_mouse_down = self
#            print "Mouse down on " + str(self)
        
        if event.type == MOUSE_UP:
            x, y = event.pos
            if Component.dragging == None and Component.last_mouse_down == self:
                # mouse down then mouse up on same component => click]
                pygame.event.post(pygame.event.Event(MOUSE_CLICK, pos = (x, y), button=event.button))
#                print "Click on " + str(self)
            else:
                if Component.dragging != None:
#                    print "Mouse dropped on " + str(self)
                    pygame.event.post(pygame.event.Event(MOUSE_DROP, dropped=Component.last_mouse_down, pos = (x, y), button=event.button))
                # notify other component that mouse was released
                if Component.last_mouse_down != None:
                    Component.last_mouse_down.event_handler(event)
#                    print "Non-click mouse up on " + str(self)
            
            Component.last_mouse_down = None
            Component.dragging = None
        
        if event.type == MOUSE_CLICK and self.takes_focus():
            Component.focus = self
        
        # TODO: generate hover events if mouse sits over one component for a while
        
#        if event.type == MOUSE_HOVER:
#            # TODO: default behavior to show tooltip
#            pass
        
        return self.event_handler(event)
    
    def disable(self):
        self.enabled = False
        
    def enable(self):
        self.enabled = True
    
    def enabled(self):
        return self.enabled;
    
    def render(self, surface, images):
        pass
    
    def paint(self, surface, images):
        if self.shown and self.enabled:
           
            self.render(surface, images)
            for child in self.children:
                child.paint(surface, images)
#            if self.tool_tip_enabled:
#                self.render_tooltip(surface, images)
    
        
            # render modal on top
            if Component.has_active_modal() and self.top_level():
                for modal_window in Component.modal_stack:
                    modal_window.paint(surface, images)
            # render tooltip on tippy top
            if Component.has_active_tooltip() and self.top_level():
                Component.render_tooltip(surface, images)
            if Component.dragging != None and self.top_level():
                #render semi-transparent version of dragged component, shifted to be under mouse cursor    
                orig_rect = Component.last_mouse_down.rect
                offset_x, offset_y = Component.dragging
                Component.last_mouse_down.rect = Rect(offset_x, offset_y, orig_rect.width, orig_rect.height)
                Component.last_mouse_down.paint(surface, images)
                Component.last_mouse_down.rect = orig_rect
            

class Window(Component):
    
    def render(self, surface, images):
        images.draw_window(surface, self.rect)  