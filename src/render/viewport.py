'''
Created on Jun 7, 2012

@author: Chris
'''
import math  
import image
from collections import namedtuple
from util.tools import Loc
from core.event_manager import Event
import core.event_manager as event_manager

ScaledHex = namedtuple('ScaledHex', ['hex_width', 'hex_height'])

class Viewport:
    '''
    classdocs
    '''

    def __init__(self, position_rect, map_width, map_height):
        # position and size of viewport within window
        self.rect = position_rect
        
        # size in hexes of underlying map
        self.map_width = map_width
        self.map_height = map_height
        self.selected_hex = None
        
        # current pixel offset within map
        self.x_offset = 0   
        self.y_offset = 0
        
        # initialize scaling values to allow zooming in/out on map
        values = ScaledHex(image.HEX_WIDTH, image.HEX_HEIGHT)
        self.scaled_hex_sizes = [values]
        for div in [2, 4]:
            self.scaled_hex_sizes.append(ScaledHex(values.hex_width/div, values.hex_height/div))
        self.scale_power = 0
        self.rescale(True)
     
    def zoom_in(self):
        return self.rescale(True)
    
    def zoom_out(self):
        return self.rescale(False)

    # zoom in or out
    def rescale(self, zoom_in):
        prev_scale_power = self.scale_power
        if zoom_in:
            self.scale_power = max(0, self.scale_power - 1)
        else:
            self.scale_power = min(len(self.scaled_hex_sizes) - 1, self.scale_power + 1)
        
        self.hex_width = self.scaled_hex_sizes[self.scale_power].hex_width
        self.hex_height = self.scaled_hex_sizes[self.scale_power].hex_height
        self.row_height = (self.hex_height * 3 ) / 4
        self.max_x = self.hex_width * self.map_width
        self.max_y = self.row_height * self.map_height
    
    def select_hex(self, hex_x, hex_y):
        if hex_x < 0 or hex_x >= self.map_width or hex_y < 0 or hex_y >= self.map_height:
            return None
        
        self.selected_hex = Loc(hex_x, hex_y)
        event_manager.queue_event(Event(event_manager.HEX_SELECTED, [self.selected_hex]))
        return self.selected_hex
    
    def select_hex_from_pixel(self, pixel_x, pixel_y):
        hex_x, hex_y = self.hex_from_pixel(pixel_x, pixel_y)
        return self.select_hex(hex_x, hex_y)
    
    def get_hex_bounds(self):
        x_start, y_start = self.x_offset / self.hex_width - 1, self.y_offset / self.row_height - 1
        x_end = (self.x_offset + self.rect.width + (self.hex_width / 2)) / self.hex_width + 1
        y_end = (self.y_offset + self.rect.height) / self.row_height + 1
        return x_start, y_start, x_end, y_end
    
    def center(self, hex_x, hex_y):
        target_center_x, target_center_y = self.pixel_from_hex(hex_x, hex_y)
        #curr_center_x, curr_center_y =   
        
        #print curr_center_x
        #print curr_center_y
        #print target_center_x
        #print target_center_y
        
        self.move(target_center_x - self.rect.width / 2, target_center_y - self.rect.height / 2)
     
    def move(self, x_adjust, y_adjust):
        self.x_offset = min(max(self.x_offset + x_adjust, 0), self.max_x - (self.rect.width - self.hex_height / 2))
        self.y_offset = min(max(self.y_offset + y_adjust, 0), self.max_y - (self.rect.height - self.hex_height / 4))
     
    
    def pixel_from_hex(self, hex_x, hex_y):
        pixel_x = (hex_x * self.hex_width) - self.x_offset
        pixel_y = (hex_y * self.row_height) - self.y_offset
        
        if hex_y % 2 != 0:
            pixel_x += self.hex_width / 2
        
        return self.rect.x + pixel_x, self.rect.y + pixel_y
    
    def hex_from_pixel(self, pixel_x, pixel_y):
        rise = self.hex_height * 0.25
        slope = rise / (self.hex_width * 0.5)
        world_x = pixel_x + self.x_offset - self.rect.x
        world_y = pixel_y + self.y_offset - self.rect.y
        
        # starting guess for hex position, assuming it is  inside the square part of the grid
        hex_x = world_x / self.hex_width   
        hex_y = world_y / self.row_height
        offset_x, offset_y = world_x - (hex_x * self.hex_width), world_y - (hex_y * self.row_height)
        
        # adjust hex position based on actual offset of mouse
        if hex_y % 2 == 0:
            if offset_y < (-slope * offset_x + rise):
                #Point is below left line; inside SouthWest neighbor.
                hex_x -= 1
                hex_y -= 1
            elif offset_y < (slope * offset_x - rise):
                #Point is below right line; inside SouthEast neighbor.
                hex_y -= 1
        else:
            if offset_x >= self.hex_width / 2: #is the point on the right side?
                if offset_y < (-slope * offset_x + rise * 2.0):
                    # Point is below bottom line; inside SouthWest neighbor.
                    hex_y -= 1
            else:  #Point is on the left side
                if offset_y < (slope * offset_x):
                    #Point is below the bottom line; inside SouthWest neighbor.
                    hex_y -= 1
                else:  
                    #Point is above the bottom line; inside West neighbor.
                    hex_x -= 1  
        
        return Loc(hex_x, hex_y)
