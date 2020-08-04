'''
Created on Jul 10, 2012

@author: Chris
'''
from util.tools import make_2D_list

VISIBLE = 0
NOT_VISIBLE = 1
NEVER_VISIBLE = 2

class Mask(object):
    '''
    classdocs
    '''

    # all_visible is for creating debug mask
    def __init__(self, player, hex_map, all_visible = False):
        self.visible_count = make_2D_list(hex_map.width, hex_map.height, (1 if all_visible else 0))
        self.ever_visible = make_2D_list(hex_map.width, hex_map.height, all_visible)
        self.hex_map = hex_map
        self.player = player
        
    def get_visible_hexes(self, hex_loc, radius):
        return self.hex_map.get_hexes_in_radius(hex_loc, radius)
        
    def get_player(self):
        return self.player

    def seer_added(self, hex_loc, sight_range):
        visible_hexes = self.get_visible_hexes(hex_loc, sight_range)
        for curr_hex in visible_hexes:
            self.visible_count[curr_hex.x][curr_hex.y] += 1
            self.ever_visible[curr_hex.x][curr_hex.y] = True
        
    def seer_removed(self, hex_loc, sight_range):
        visible_hexes = self.get_visible_hexes(hex_loc, sight_range)
        for curr_hex in visible_hexes:
            self.visible_count[curr_hex.x][curr_hex.y] -= 1
    
    def visibility_changed(self, hex_loc, old_range, new_range):
        self.seer_removed(hex_loc, old_range)
        self.seer_added(hex_loc, new_range)
     
    def get_visibility(self, x, y):
        if x < 0 or y < 0 or x >= self.hex_map.width or y >= self.hex_map.height:
            return NEVER_VISIBLE
        
        if self.visible_count[x][y] > 0:
            return VISIBLE
        elif self.ever_visible[x][y]:
            return NOT_VISIBLE
        return NEVER_VISIBLE