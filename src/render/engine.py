'''
Created on Jul 12, 2012

@author: Chris
'''
'''
Created on Jun 7, 2012

@author: Chris
'''
import pygame
import map_render, hex_info_panel, combat_panel, viewport, status_panel, loot_panel, control_panel, popup, gui.modal as modal, unit_panel
#from gui.textbox import TextBox
from gui.component import Component
import gui.component as component
import file.save_load as save_load
from hexcrawl.misc_commands import EndTurnCommand
import core.process_manager as process_manager, core.event_manager as event_manager
from core.event_manager import Event
from util.tools import Rect
import sound

FRAMES_PER_SEC = 40 # target 60 fps

engine_events = [event_manager.TURN_END,  event_manager.MOVE_DONE, event_manager.MODAL_DIALOG, 
                 event_manager.PLAYER_LOST, event_manager.PLAYER_WON, #event_manager.GAME_OVER,
                 event_manager.COMMAND_ISSUED, event_manager.QUIT]

class GameEngine(Component):
    
    def __init__(self, pixel_dimensions, image_mgr, sound_mgr):
        self.width, self.height = pixel_dimensions
        super(GameEngine, self).__init__(Rect(0, 0, self.width, self.height))
        
        self.display_surf = pygame.display.get_surface()
        self.save_on_quit = True
    
        self.sounds = sound_mgr
        self.images = image_mgr
      
        self.unit_renderer = unit_panel.UnitRenderer( Rect( (self.width * 4) / 5, self.height / 6, self.width / 5, self.height / 2), self.images )
        self.map_renderer = map_render.MainMap()
        self.hex_info_renderer = hex_info_panel.HexInfoRenderer(Rect(0, (self.height * 2) / 3, (self.width * 4) /5, self.height / 3), self.images)
        self.status_renderer = status_panel.StatusRenderer(Rect(0, 0, self.width, 34))
        self.control_panel = control_panel.ControlRenderer(Rect((self.width * 4)/5, (self.height * 2) / 3,
                                                                self.width / 5, self.height / 3), self.images, self)
        
        # order = layering, will draw earlier children first and send them events last, so 'bottom' layer comes first
        children = [self.map_renderer, self.unit_renderer, self.hex_info_renderer, self.control_panel,
                    self.status_renderer] 
        for child in children:
            self.add_child(child)
        
        self.curr_group = None
        self.curr_site = None
        self.paused = False
        self.quit_to_desktop = False
     
    def post_load_init(self):
        self.debug_mask_on = False
        self.active_mask = self.curr_game.get_mask()
        self.sounds.set_mask(self.active_mask)
        self.sounds.do_soundtrack(sound.BACKGROUND_MUSIC)
        
        event_manager.add_listener_multi(self.handle_game_events, engine_events)
        Component.set_top_level(self, self.width, self.height, self.width/2, self.height/3)
        self.combat_renderer = combat_panel.CombatRenderer(Rect(self.width/5, self.height/5, (3 *self.width)/5, (3 *self.height)/8), self.images)
        self.loot_renderer = loot_panel.LootRenderer(Rect(self.width/4, self.height/4, self.width/2, self.height/4))
        
        self.popup_renderer = popup.PopupRenderer()
        self.show()
        self.mini_renderer.hide()
        self.update_window_data()

    def update_window_data(self):
        self.map_renderer.set_data(self.curr_game.get_map(), self.curr_game.get_curr_player(), self.active_mask)
        self.mini_renderer.set_data(self.curr_game.get_map(), self.active_mask)
        self.hex_info_renderer.set_data(self.curr_game.get_map(), self.curr_game.get_curr_player(), self.active_mask)
        self.status_renderer.set_data(self.curr_game.get_map(), self.curr_game.get_curr_player(), self.active_mask, self.curr_game.get_turn())
        self.combat_renderer.set_data(self.map_renderer, self.active_mask)
        self.unit_renderer.set_data(self.curr_game.get_map(), self.images)
        self.loot_renderer.set_data(self.active_mask)
        self.popup_renderer.set_data(self.map_renderer, self.active_mask)
        
    def start(self, game, initial_view=None):
        self.curr_game = game
        new_game = False
        if initial_view == None:
            new_game = True
            initial_view = viewport.Viewport(Rect(0, 34, self.width, (self.height * 2) / 3 - 34), 
                                                self.curr_game.get_map().width, self.curr_game.get_map().height)
        self.map_renderer.set_view(initial_view)
#        self.mini_renderer = map_render.MiniMap(Rect(0, self.height / 6, self.width / 3, self.height / 2), 
#                                                self.curr_game.get_map().width, self.curr_game.get_map().height)
        self.mini_renderer = map_render.MiniMap(0, (self.height * 2)/3,
                                                self.curr_game.get_map().width, self.curr_game.get_map().height)
        self.mini_renderer.set_main_view(initial_view)
        self.add_child(self.mini_renderer)
       
#        self.mini_renderer.set_view(viewport.Viewport(Rect(0, 34, self.width /3, (self.height * 2) / 3 - 34), 
#                                                self.curr_game.get_map().width, self.curr_game.get_map().height, scale_power = 3))
       
        start_hex = self.curr_game.get_start_hex()
        self.map_renderer.center(start_hex.x, start_hex.y) 
        self.post_load_init()
        
        game.initialize(new_game)
#        if new_game:
#            game.start()

    def select_hex(self, hex_x, hex_y):
        self.map_renderer.select_hex(hex_x, hex_y)
        
    def move_to_hex(self, move_hex):
        self.select_hex(move_hex.x, move_hex.y)
        self.center_view()
    
    def end_turn(self):
        command = EndTurnCommand(self.active_mask.get_player())
        event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
    
    def tools(self):
        if self.activity_allowed:
            tools_dialog = modal.ToolsDialog(400, 300, "Tools")
            tools_dialog.show()
    
    def next_group(self):
        if self.curr_group == None:
            self.curr_group = self.active_mask.get_player().get_first_group()
        else:
            self.curr_group = self.curr_group.get_next()
        self.move_to_hex(self.curr_group.get_hex())
        
    def previous_group(self):
        if self.curr_group == None:
            self.curr_group = self.active_mask.get_player().get_last_group()
        else:
            self.curr_group = self.curr_group.get_previous()
        self.move_to_hex(self.curr_group.get_hex())

    def next_site(self):
        if self.curr_site == None:
            self.curr_site = self.curr_game.get_curr_player().get_first_site()
        else:
            self.curr_site = self.curr_site.get_next()
        self.move_to_hex(self.curr_site.get_hex())
    
    def previous_site(self):
        if self.curr_site == None:
            self.curr_site = self.curr_game.get_curr_player().get_last_site()
        else:
            self.curr_site = self.curr_site.get_previous()
            
        self.move_to_hex(self.curr_site.get_hex())

    def center_view(self):
        selected_hex = self.map_renderer.view.selected_hex
        if selected_hex != None:
            self.map_renderer.center(selected_hex.x, selected_hex.y) 
    
    def toggle_zone_borders(self):
        self.map_renderer.toggle_zone_borders()
    
    def minimap(self):
        if self.mini_renderer.is_shown():
            self.mini_renderer.hide()
        else:
            self.mini_renderer.show()

    def handle_game_events(self, event):
        if event.type == event_manager.MOVE_DONE:
            # if the moving player is the one seeing these events, update his selected hex to the
            # hex just moved to
            if event.data['group'].get_owner() == self.active_mask.get_player():
                new_hex = event.data['hex_loc']
                self.select_hex(new_hex.x, new_hex.y)
        elif event.type == event_manager.PLAYER_WON:
            self.save_on_quit = False
            if event.data['player'] == self.active_mask.get_player():
                game_over_dialog = modal.TextDialog("Victory!", event.data['description'],
                                                        close_event =  Event(event_manager.QUIT, [False]))
            else:
                game_over_dialog = modal.TextDialog("You Lost!", event.data['description'],
                                                        close_event =  Event(event_manager.QUIT, [False]))
            
            game_over_dialog.open_window()
        elif event.type == event_manager.PLAYER_LOST:
            self.save_on_quit = False
            if event.data['player'] == self.active_mask.get_player():
                game_over_dialog = modal.TextDialog("You Lost!", event.data['description'], 
                                                    close_event =  Event(event_manager.QUIT, [False]))
                game_over_dialog.show()
                self.paused = True
        elif event.type == event_manager.QUIT:
            if event.data['save']:
                save_load.save_game(self.curr_game, self.map_renderer.view)
            self.sounds.stop_soundtrack()
            self.curr_game.do_cleanup()
            process_manager.abort_all_processes()
            event_manager.reset()
            Component.clear_modals()
            self.running = False
        elif event.type == event_manager.TURN_END:
            if self.debug_mask_on:
                self.active_mask = self.curr_game.get_debug_mask() 
            else:
                self.active_mask = self.curr_game.get_mask()
            self.curr_group = None
            self.update_window_data()
#            self.hex_info_renderer.set_hex(self.map_renderer.view.selected_hex)
        elif event.type == event_manager.COMMAND_ISSUED:
            self.curr_game.handle_command(event.data['command'])
            self.activity_allowed = False

    def event_handler(self, event):
        if event.type == component.TICK:
            event_manager.queue_event(Event(event_manager.TICK, []))
            return True
        # redirect arrow events to map:
        if event.type == component.KEY_UP or event.type == component.KEY_DOWN:
            if (event.key == component.K_DOWN or event.key == component.K_UP or
                event.key == component.K_LEFT or event.key == component.K_RIGHT):
                return self.map_renderer.event_handler(event)
        
        if event.type == component.KEY_DOWN: 
#            if (event.key == pygame.K_z):
#                self.view.zoom_out()
#            elif (event.key == pygame.K_a):
#                self.view.zoom_in() 
            if (event.key == pygame.K_m):
                self.minimap()
            elif (event.key == pygame.K_b):
                self.toggle_zone_borders()
            elif (event.key == pygame.K_n):
                self.next_group()
            elif (event.key == pygame.K_p):
                self.previous_group() 
            elif (event.key == pygame.K_a):
                self.previous_site()
            elif (event.key == pygame.K_s):
                self.next_site() 
            elif (event.key == pygame.K_g):
                if self.debug_mask_on:
                    self.active_mask = self.curr_game.get_mask()
                    self.debug_mask_on = False
                else:
                    self.debug_mask_on = True
                    self.active_mask = self.curr_game.get_debug_mask()
                self.update_window_data()
            elif (event.key == pygame.K_e and self.activity_allowed):
                return self.end_turn()
            elif (event.key == pygame.K_c and self.activity_allowed):
                self.center_view()
        elif event.type == pygame.QUIT:
            self.quit_to_desktop = True
            event_manager.queue_event(Event(event_manager.QUIT, [self.save_on_quit]))

    def handle_events(self, events):
        for event in events:
                if event.type == component.MUSIC_DONE:
                    self.sounds.do_soundtrack(sound.BACKGROUND_MUSIC)
                elif event.type == component.AUTOSAVE:
                    save_load.save_game(self.curr_game, self.map_renderer.view)
                else:
                    self.on_ui_event(event)
      
    def main_loop(self):
        prev_time = pygame.time.get_ticks()
        game_clock = pygame.time.Clock()

        self.running = True
        self.activity_allowed = True
    
        TICK_INTERVAL = 1000 / FRAMES_PER_SEC 
        pygame.time.set_timer(component.TICK, TICK_INTERVAL)
        pygame.time.set_timer(component.AUTOSAVE, component.AUTOSAVE_INTERVAL)
        
        while (self.running):    
                    
            # if UI locked, unlock it if no modals or on-going processes 
            if not self.activity_allowed and process_manager.get_process_count() == 0:
                self.activity_allowed = True
                
            self.handle_events(pygame.event.get())
            event_manager.tick_update()
            
            if not self.paused:
                # update ongoing processes
                curr_time = pygame.time.get_ticks()
                process_manager.update_processes(curr_time - prev_time)
                prev_time = curr_time
                             
            self.display_surf.fill((0, 0, 0))
            self.paint(self.display_surf, self.images)

            pygame.display.flip()
            game_clock.tick(FRAMES_PER_SEC)
#            event_manager.queue_event(Event(event_manager.TICK, []))
            
        
        return self.quit_to_desktop
            
    
            
            

