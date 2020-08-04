'''
Created on Aug 9, 2012

@author: Chris
'''

curr_options = None

SLOW_COMBAT_SPEED = 0
MED_COMBAT_SPEED = 1
FAST_COMBAT_SPEED = 2

class Options(object):
    
    def __init__(self):
        self.sound = True
        self.sound_volume = 1.0
        self.music = True
        self.music_volume = 0.5
        self.own_combat_speed = MED_COMBAT_SPEED
        self.other_combat_speed = MED_COMBAT_SPEED
        self.player_name = "Order"
        self.font = "Graverplate Bold.ttf"
