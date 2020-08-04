'''
Created on Jul 25, 2012

@author: Chris
'''
import core.event_manager as event_manager
import core.options as options
import pygame.mixer 
import os, random
import gamemap.mask as mask
import gui.component as component

sound_events = [event_manager.UNIT_BLOCK, event_manager.UNIT_HEAL, event_manager.UNIT_HIT, event_manager.RANGED_ATTACK,
                event_manager.MOVE_DONE, event_manager.TURN_START,
                event_manager.COMBAT_START, event_manager.COMBAT_END, event_manager.BUTTON_CLICK,
                event_manager.MUSIC_CHANGE]

combat_sound_events = [event_manager.UNIT_BLOCK, event_manager.UNIT_HEAL, event_manager.UNIT_HIT, event_manager.RANGED_ATTACK]

sound_file_table = {event_manager.UNIT_BLOCK: "block.wav", event_manager.UNIT_HEAL: "angel.wav", 
                    event_manager.UNIT_HIT: "grunt.wav", event_manager.MOVE_DONE: "march.wav",
                    event_manager.RANGED_ATTACK: "twang.wav", event_manager.TURN_START: "turn.wav",
                    event_manager.BUTTON_CLICK: "click.wav"}

TITLE_MUSIC = "Title music"
BACKGROUND_MUSIC = "Background music"

title_music = ["greensleeves-francis.mp3"]
background_music = ["crooked-corsair-inn.mp3", "into-the-abyss.mp3", "land-of-fantasy.mp3"]
                   #"PraetoriusBransle.ogg"]
music_tracks = {TITLE_MUSIC: title_music, BACKGROUND_MUSIC: background_music}

class SoundManager(object):
    
    def __init__(self):
        self.mask = None
        self.active_combat = False
        self.sound_active = True
#        self.paused_music = None
        
        pygame.mixer.init()
        self.sound_table = {}
        for sound_event in sound_file_table:
            self.sound_table[sound_event] = self.prep_sound_file(sound_file_table[sound_event])
    
    def initialize(self):
        event_manager.add_listener_multi(self.handle_event, sound_events)
        pygame.mixer.music.set_endevent(component.MUSIC_DONE)
    
    
#    def do_battle_music(self):
#        if  options.curr_options.music:
#            pygame.mixer.music.load(os.path.join('data', 'music', "kings-valor.mp3"))
#            pygame.mixer.music.set_volume(options.curr_options.music_volume)
#            pygame.mixer.music.play()
    
    def do_soundtrack(self, mode):
        if options.curr_options.music:
            music_file_name = random.choice(music_tracks[mode])
            pygame.mixer.music.load(os.path.join('data', 'music', music_file_name))
            pygame.mixer.music.set_volume(options.curr_options.music_volume)
            pygame.mixer.music.play()
  
        else:
            self.stop_soundtrack()
#    
    def stop_soundtrack(self):
        pygame.mixer.music.stop()    
    
    def handle_event(self, event):
        if event.type == event_manager.MUSIC_CHANGE:
            options.curr_options.music = event.data['on']
            self.do_soundtrack(BACKGROUND_MUSIC)
            return
#            
#            if event.data['on']:
#                self.start_soundtrack()
#            else:
#                self.stop_soundtrack()
#            return
        
        play_sound = options.curr_options.sound
        
        if event.type == event_manager.COMBAT_START:
            loc = event.data['hex_loc']
            if self.mask != None and self.mask.get_visibility(loc.x, loc.y) == mask.VISIBLE: 
#                print "visible combat!"
                self.active_combat = True
#                self.do_battle_music()
            play_sound = False
        elif event.type == event_manager.COMBAT_END:
#            if self.active_combat:
#                self.do_soundtrack(BACKGROUND_MUSIC)
            self.active_combat = False
            play_sound = False
             
        elif event.type == event_manager.MOVE_DONE:
            end_loc = event.data['hex_loc']
            start_loc = event.data['hex_start']
            if end_loc == start_loc or self.mask == None or self.mask.get_visibility(end_loc.x, end_loc.y) != mask.VISIBLE:
                play_sound = False
        elif event.type == event_manager.TURN_START:
            if event.data['player'] != self.mask.get_player():
                play_sound = False
        elif event.type in combat_sound_events:
            # play only if there's an active combat visible to player
            play_sound = play_sound and self.active_combat
                
        if play_sound:
            self.sound_table[event.type].play()
    
    def set_mask(self, new_mask):
        self.mask = new_mask
    
    def prep_sound_file(self, file_name):
        
        return pygame.mixer.Sound(os.path.join('data', 'sound', file_name))
    
    