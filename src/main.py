'''
Created on Jun 7, 2012

@author: Chris
'''
#from pgu import gui
import pygame, sys, random, os
import render.engine as engine
import file.save_load as save_load
import render.gui.component as component
import render.image as image, render.sound as sound
from render.gui.component import Component
from render.gui.button import Button, ToggleGroup
from render.gui.textbox import TextBox
from render.gui.label import Label
from render.gui.modal import TextDialog
from util.tools import Rect
from file.data_loader import DataLoader
import core.event_manager as event_manager
import thread, time
import hexcrawl.game as game
import core.options as options
import render.text as text

NO_ACTIVITY = 0
PREPARING = 1
READY = 2

map_size_table  = [(36, 36),(54, 54), (72, 72)]
DEFAULT_MAP_SIZE = 1
DEFAULT_PLAYER_NAME = "Party"

class MainMenu(component.Window):

    def __init__(self, (width, height)):
        super(MainMenu, self).__init__(Rect(0, 0, width, height))
        pygame.init()
        pygame.display.set_mode((self.rect.width, self.rect.height), pygame.HWSURFACE)
    
        DataLoader.load_data() 
        options.curr_options = save_load.load_options()
        self.image_mgr = image.ImageManager(options.curr_options.font)
        self.sound_mgr = sound.SoundManager()
       
        
        self.initialize()
        
    def take_gui_control(self):
        Component.set_top_level(self, self.rect.width, self.rect.height)
    
    def initialize(self):
        self.seed =  random.randint(0, sys.maxint)
        self.engine = None
        self.ready_game = None
        self.ready_view = None
        self.game_status = NO_ACTIVITY
        self.sound_mgr.initialize()
        self.image_mgr.initialize()
        self.take_gui_control()
        self.build_ui()
        self.sound_mgr.do_soundtrack(sound.TITLE_MUSIC)
    
    def build_ui(self):
        small_pad = 4
        big_pad = 20
        
        self.clear_children()
         
        width, height = self.image_mgr.banner.get_width(), self.image_mgr.banner.get_height()
        x, y = self.rect.width/2 - width/2, big_pad
        self.add_child(Label(Rect(x, y, width, height), self.image_mgr.banner, image_label=True))
        y += height + big_pad
        

        label_width = 60
        toggle_width = 240
        button_width = 120
        button_height = 40
        
        x = big_pad * 2
        self.add_child(Label(Rect(x, y, label_width, button_height), "Faction:", font=text.lg_font))
        x += label_width + small_pad
        
        def player_name_callback(name_text):
            self.player_name = name_text
        
        self.player_name = options.curr_options.player_name
        self.add_child(TextBox(Rect(x, y - 5, label_width * 2, 50), 10, player_name_callback, self.player_name))
        x += label_width * 2 + small_pad

        self.add_child(Label(Rect(x, y, label_width, button_height), "Map size:", font=text.lg_font))
        
        def map_size_callback(index):
            self.map_size = map_size_table[index]
        
        x += label_width + small_pad
        self.map_size = map_size_table[DEFAULT_MAP_SIZE]
        self.add_child(ToggleGroup(Rect(x, y, toggle_width, button_height), ["Small", "Medium", "Large"], 
                                           map_size_callback, default_index=DEFAULT_MAP_SIZE))       

        def start_button_callback():
            game_params = game.GameParams(self.map_size, self.seed, self.player_name)
            thread.start_new_thread(self.create_game, (game_params, ))
           
            # dump the seed value to a file in case this game needs to be recreated
            seed_file = open('recent_seeds.txt', 'a')
            seed_file.write(str(self.seed) + "\n")
            
            # save player name to options
            options.curr_options.player_name = self.player_name
        
        x += toggle_width + big_pad *2
        self.add_child(Button( Rect(x, y, button_width, button_height), "New Game", start_button_callback))
        
        if save_load.can_load_game():
            def continue_button_callback():
                thread.start_new_thread(self.load_game, ("", ))
                
            x += button_width + big_pad
           
            self.add_child(Button( Rect(x, y, button_width, button_height), "Continue Game", continue_button_callback))

        
        y += big_pad * 2
        x = self.rect.width / 2 - label_width / 2
        self.status_label = Label(Rect(x, y, label_width, button_height), None, font=text.lg_font)
        self.add_child(self.status_label)
        
        def exit_button_callback():
            self.running = False
            
        x = self.rect.width - button_width - big_pad * 2 
        y = self.rect.height - button_height - big_pad *2
        self.add_child(Button( Rect(x, y, button_width, button_height), "Exit", exit_button_callback))

        x = self.rect.x + big_pad * 2
        self.add_child(Button( Rect(x, y, button_width, button_height), "Tutorial", exit_button_callback))
        x += button_width + big_pad
        
        def credits_button_callback():
            credit_text = "Design, Programming, Art, Sound: Chris McDonald\n\n" + \
                          "Production: Julie McDonald" + \
                          "\n\nTesting: Stephen Chu, Matthew Cosner\n\n\n" + \
                          "     Copyright 2012"
            credits_dialog = TextDialog("Credits", credit_text)
            credits_dialog.show()
            
        self.add_child(Button( Rect(x, y, button_width, button_height), "Credits", credits_button_callback))
        
    def game_prep(self, prep_status, prep_func):
        self.game_status = PREPARING
        self.status_label.set_label(prep_status)
        prep_func()
        self.status_label.set_label(None)
        self.engine = engine.GameEngine((self.rect.width, self.rect.height), self.image_mgr, self.sound_mgr)
        self.game_status = READY

    def create_game(self, game_params):
        def make_game():
            self.ready_game = game.Game(game_params)
        self.game_prep("Preparing Game...", make_game)
  
    def load_game(self, game_file):
        def get_game():
            self.ready_game, self.ready_view = save_load.load_game()
        self.game_prep("Loading Game...", get_game)
  
    def run(self):
        pygame.display.set_caption("HexCrawler")
        icon = pygame.image.load(os.path.join('data', 'img', 'ui', "icon.png"))
        pygame.display.set_icon(icon)

        self.show()
        self.running = True
        # transition to main game
        while self.running:
            for event in pygame.event.get():
                
                if (event.type == pygame.QUIT or 
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
                else:
                    if self.game_status != PREPARING:
                        self.on_ui_event(event)
                    
            self.paint(pygame.display.get_surface(), self.image_mgr)
            pygame.display.flip()        
            
            if self.game_status == PREPARING:
                time.sleep(0.05)
                continue
                        
            event_manager.tick_update()
                    
            if self.game_status == READY:
                self.engine.start(self.ready_game, self.ready_view)
                quit_to_desktop = self.engine.main_loop()
                if quit_to_desktop:
                    self.running = False
                self.initialize()
                self.show()
        
        save_load.save_options()
    
          
if __name__ == '__main__':
    dim = (1048, 640)
    app = MainMenu(dim)
    app.run()
