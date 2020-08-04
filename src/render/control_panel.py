'''
Created on Jul 18, 2012

@author: Chris
'''
import image
from util.tools import Rect, inside
from gui.button import Button
import gui.component as component

class ControlRenderer(component.Window):
    '''
    classdocs
    '''


    def __init__(self, position_rect, images, handler):
        super(ControlRenderer, self).__init__(position_rect)
        '''
        Constructor
        '''
        pad = 16
        top_pad = 16
#        self.rect = position_rect
        handlers = [handler.previous_group, handler.next_group, handler.previous_site, handler.next_site, handler.center_view, handler.end_turn, handler.tools]
        image_labels = [images.l_arrow, images.r_arrow, images.prev_site, images.next_site, images.center_view, images.end_turn, images.tools]
        tool_tips = ["prev. group (p)", "next group(n)", "prev. site (a)", "next site(s)","center (c)", "end turn (e)", "tools"]
        x, y = self.rect.x + pad, self.rect.y + top_pad
        width, height = image.CONTROL_BUTTON_WIDTH, image.CONTROL_BUTTON_HEIGHT
        for i in range(len(handlers)):
            self.add_child(Button(Rect(x, y, width, height), image_labels[i], handlers[i], image_label = True,  tool_tip_text = tool_tips[i]))
            x += image.CONTROL_BUTTON_WIDTH + pad 
            if x > self.rect.x + self.rect.width - image.CONTROL_BUTTON_WIDTH:
                x = self.rect.x + pad
                y += image.CONTROL_BUTTON_HEIGHT + top_pad               
                         
#    def handle_mouse(self, x, y):
#        for curr_button in self.buttons:
#            if inside(curr_button.rect, x, y):
#                return curr_button.handle_mouse(x, y)
    
#    def render(self, surface, images):
##        surface.fill((0, 127, 127), self.rect)
#       
#        for curr_button in self.buttons:
#            curr_button.render(surface, images)
#        surface.blit(images.l_arrow, (self.l_arrow_rect.x, self.l_arrow_rect.y))
#        surface.blit(images.r_arrow, (self.r_arrow_rect.x, self.r_arrow_rect.y))
#        surface.blit(images.center_view, (self.center_view_rect.x, self.center_view_rect.y))
#        surface.blit(images.end_turn, (self.end_turn_rect.x, self.end_turn_rect.y))
          
        