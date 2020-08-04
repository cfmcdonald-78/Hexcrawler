'''
Created on Jun 6, 2012

@author: Chris
'''
import gamemap.mask as mask
import gamemap.site as site
import pygame
import gamemap.hexgrid as hexgrid
import mob.group as group, mob.move_mode as move_mode
import image
from util.tools import Rect
import gui.component as component
from hexcrawl.movement import MoveCommand
from core.event_manager import Event
import core.event_manager as event_manager
import text
import viewport

MOVE_INCREMENT = 12
MAX_BAR_WIDTH = (image.HEX_WIDTH - 16)
map_events = [event_manager.TICK, event_manager.MAP_ATTACK_DONE, event_manager.MAP_ATTACK_FIRE, 
              event_manager.MAP_ATTACK_HIT, event_manager.MAP_ATTACK_BLOCK]

def hex_line(surface, center, color, direction):
        pygame.draw.line(surface, color, hexgrid.side_midpt(center, 3.5, direction), center, 2)

class MiniMap(component.Window):
    def __init__(self, x_left, y_bottom, hex_width, hex_height):
        width = hex_width * 6
        height = hex_height * 6 
        super(MiniMap, self).__init__(Rect(x_left, y_bottom - (height + 24), width + 24, height + 24))
        self.map_data = None
        self.curr_mask = None
        self.view = viewport.Viewport(Rect(x_left + 12, y_bottom - (height + 24) + 12, width, height), 
                                      hex_width, hex_height, scale_power = 3)
    
    
    
    def set_main_view(self, main_view):
        self.main_view = main_view
        
    def set_data(self, map_data, curr_mask):
        self.map_data = map_data
        self.curr_mask = curr_mask
        
    def event_handler(self, event):
        if event.type == component.MOUSE_DOWN:
            x, y = event.pos
            if event.button == component.LEFT_MOUSE:
                hex_x, hex_y = self.view.hex_from_pixel(x, y)
                self.main_view.center(hex_x, hex_y)
#                self.select_hex(hex_x, hex_y)
                
        return super(MiniMap, self).event_handler(event)
                
    
    
    def render(self, surface, images):
        super(MiniMap, self).render(surface, images)
        x_start, y_start, x_end, y_end = self.view.get_hex_bounds()
        
        for hex_y in range(y_start, y_end):
            for hex_x in range(x_start, x_end):
                curr_hex = self.map_data.get_hex(hex_x, hex_y)
                if curr_hex == None:
                    continue
            
                pixel_x, pixel_y = self.view.pixel_from_hex(hex_x, hex_y)
                center = (pixel_x + 4, pixel_y + 4)
                
                visibility = self.curr_mask.get_visibility(hex_x, hex_y)
                if visibility == mask.NEVER_VISIBLE:
                    surface.blit(images.mini_invisible_hex, (pixel_x, pixel_y))
                    continue
                
                
                hex_image = images.hex_image(curr_hex.hex_type, hex_x + hex_y * self.view.get_hex_width(), mini=True)
                surface.blit(hex_image, (pixel_x, pixel_y))
                
                if curr_hex.river != None:
                    for direction in curr_hex.river.in_flows:
                        hex_line(surface, center, (45, 84, 153), direction)
                    hex_line(surface, center, (45, 84, 153), curr_hex.river.out_flow)
                
                if curr_hex.road != None:
                    for direction in curr_hex.road.connections:
                        hex_line(surface, center, (116, 65, 30), direction)
                    
                
                site = curr_hex.site
                if site != None and site.is_active():
                    site_color = site.get_owner().get_color(site, self.curr_mask.get_player())
                    surface.fill(site_color, (pixel_x + 2, pixel_y + 2, 4, 4))
                
        pixel_offset_x, pixel_offset_y = self.main_view.get_pixel_offset()
        pixel_offset_x /= 9
        pixel_offset_y /= 8
        pygame.draw.rect(surface, (230, 230, 230), (self.view.rect.x + pixel_offset_x, self.view.rect.y + pixel_offset_y,
                                                    self.main_view.get_pixel_width() / 9, self.main_view.get_pixel_height()/8), 1)
                                                    
    
class MainMap(component.Component):
    '''
    classdocs
    '''
    def __init__(self): #,map_data):
        #self.map_data = map_data
        super(MainMap, self).__init__(None)
        self.selected_hex = None
        self.map_data = None
        self.curr_mask = None
        self.curr_player = None
        self.x_adjust, self.y_adjust = 0, 0 # amount to move view at each tick
        self.legal_moves = []
        self.map_attack_event = {}
        self.show_borders = True
        
        event_manager.add_listener_multi(self.handle_game_events, map_events)
#        event_manager.add_listener(self.handle_game_events, event_manager.HEX_SELECTED)
    
    def handle_game_events(self, event):
        if event.type == event_manager.TICK:
            self.view.move(self.x_adjust, self.y_adjust)
        elif event.type == event_manager.MAP_ATTACK_FIRE:
            self.map_attack_event[event.data['origin_loc']] = event_manager.RANGED_ATTACK
#            print "map handled start at " + str(event.data['origin_loc'])
#            if self.curr_mask.get_visibility(origin_loc.x, origin_loc.y) == mask.VISIBLE: 
#                self.map_attacks[origin_loc] = None
        elif event.type == event_manager.MAP_ATTACK_HIT:
            self.map_attack_event[event.data['target_loc']] = event_manager.UNIT_HIT
#            print "map handled hit at " + str(event.data['target_loc'])
        elif event.type == event_manager.MAP_ATTACK_BLOCK:
            self.map_attack_event[event.data['target_loc']] = event_manager.UNIT_BLOCK
#            print "map handled block at " + str(event.data['target_loc'])
        elif event.type == event_manager.MAP_ATTACK_DONE:
            "finished map attack from " + str(event.data['origin_loc']) + "to " + str(event.data['target_loc'])
            del self.map_attack_event[event.data['origin_loc']]
            del self.map_attack_event[event.data['target_loc']]
        
    def set_view(self, view):
        self.view = view
        self.rect = view.rect

    def center(self, hex_x, hex_y):
        self.view.center(hex_x, hex_y)
        self.x_adjust = 0
        self.y_adjust = 0
    
    def toggle_zone_borders(self):
        self.show_borders = not self.show_borders
    
    def set_data(self, map_data, curr_player, curr_mask):
        self.map_data = map_data
        self.curr_mask = curr_mask
        self.curr_player = curr_player
        self.update_legal_moves()
    

#    def hex_debug_text(self, surface, view, hex_x, hex_y, pixel_x, pixel_y):
#        font = pygame.font.Font(None, 12) 
#        text =   str(hex_x) + "," + str(hex_y)
#        rendered_text = font.render(text, True, (255, 255, 255), (159, 182, 205))
#
#        textRect = rendered_text.get_rect()
#        
#        # Center the text in the hex
#        textRect.centerx = pixel_x + 32 #view.HEX_WIDTH / 2
#        textRect.centery = pixel_y + 32 #view.HEX_HEIGHT / 2
#        surface.blit(rendered_text, textRect)
    
    def update_legal_moves(self):
        if self.view.selected_hex == None:
            self.legal_moves = []
            return
            
        hex_x, hex_y = self.view.selected_hex
        if self.curr_mask.get_visibility(hex_x, hex_y) == mask.VISIBLE:
            self.legal_moves = self.map_data.get_legal_moves_from(hex_x, hex_y, self.curr_mask.get_player())
        else:
            self.legal_moves = []
            
    def select_hex(self, hex_x, hex_y):
        self.view.select_hex(hex_x, hex_y)
        self.update_legal_moves()
    
    def event_handler(self, event):
        if event.type == component.MOUSE_DOWN:
            x, y = event.pos
            if event.button == component.LEFT_MOUSE:
                hex_x, hex_y = self.view.hex_from_pixel(x, y)
                self.select_hex(hex_x, hex_y)
#
            elif event.button == component.RIGHT_MOUSE:
                if self.view.selected_hex != None:
                    command = MoveCommand(self.view.selected_hex, self.view.hex_from_pixel(x, y))
                    event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
            return True
        elif event.type == component.MOUSE_HOVER:
            x, y = event.pos
            hex_x, hex_y = self.view.hex_from_pixel(x, y)
            visibility = self.curr_mask.get_visibility(hex_x, hex_y)
            if visibility == mask.NEVER_VISIBLE:
                return True
            
            hover_hex = self.map_data.get_hex(hex_x, hex_y)
            if hover_hex == None:
                return True
            
            hex_type = hover_hex.hex_type
            
            hover_text = hex_type.name + "\n"
            hover_text += "Move cost: " + str(hex_type.move_cost)
            if hex_type.required_trait != None:
                hover_text += "\nRequires: " + hex_type.required_trait
    
            # TODO: add info about river if present
            
            if visibility == mask.VISIBLE:
                hex_group = hover_hex.get_defenders()
                if hex_group != None:
                    hover_text += "\n\n" + hex_group.get_owner().get_name()
                    if hex_group.is_hostile(self.curr_mask.get_player()):
                        hover_text += "\nHostile"
            # TODO: end tooltip if view moves
            
            component.Component.set_tooltip(hover_text, (x, y))
            return True
        
        elif event.type == component.KEY_DOWN:
            if (event.key == component.K_DOWN):
                self.y_adjust = MOVE_INCREMENT
                return True
            elif (event.key == component.K_UP):
                self.y_adjust = -MOVE_INCREMENT 
                return True  
            elif (event.key == component.K_LEFT):
                self.x_adjust = -MOVE_INCREMENT
                return True
            elif (event.key == component.K_RIGHT):
                self.x_adjust = MOVE_INCREMENT  
                return True 
        elif event.type == component.KEY_UP:
            if (event.key == component.K_DOWN or event.key == component.K_UP):
                self.y_adjust = 0  
                return True
            if (event.key == component.K_LEFT or event.key == component.K_RIGHT):
                self.x_adjust = 0 
                return True
        
        return super(MainMap, self).event_handler(event)
       
    def draw_unit_bar(self, surface, images, draw_group, image_x, pixel_y, group_site):
        
        status_rect = Rect(image_x, pixel_y + image.MAP_UNIT_HEIGHT - 10, 10, 10)
        bar_width = (draw_group.num_live_units() * MAX_BAR_WIDTH) / group.MAX_UNITS
        bar_rect = Rect(status_rect.x + status_rect.width, status_rect.y + 2, bar_width, status_rect.height - 4)
        
        bar_color = draw_group.get_owner().get_color(group_site if group_site != None else draw_group, self.curr_mask.get_player())
        # TODO: get these colors from image module
        if draw_group.wounded():
            status_color = (255, 0, 0)
        elif draw_group.healthy():
            status_color = (0, 255, 0)
        else:
            status_color = (255, 255, 0)
        surface.fill(bar_color, bar_rect)
        surface.fill(status_color, status_rect)
        pygame.draw.rect(surface, (10, 10, 10), status_rect, 1)
        pygame.draw.rect(surface, bar_color, (bar_rect.x, bar_rect.y, MAX_BAR_WIDTH, bar_rect.height), 1)
        images.text.draw_text(str(draw_group.get_level()), text.vsm_font, 
                             status_rect.x + 5, status_rect.y + 5, surface)

    def render(self, surface, images):
        x_start, y_start, x_end, y_end = self.view.get_hex_bounds()
            
        for hex_y in range(y_start, y_end):
            for hex_x in range(x_start, x_end):
                curr_hex = self.map_data.get_hex(hex_x, hex_y)
                if curr_hex == None:
                    continue
                
                pixel_x, pixel_y = self.view.pixel_from_hex(hex_x, hex_y)
      
                visibility = self.curr_mask.get_visibility(hex_x, hex_y)
                if visibility == mask.NEVER_VISIBLE:
                    surface.blit(images.invisible_hex, (pixel_x, pixel_y))
                    continue
                
                surface.blit(images.hex_image(curr_hex.hex_type, hex_x + hex_y * self.view.get_hex_width()), (pixel_x, pixel_y))
                
                river = curr_hex.river
                if river != None:
                    images.draw_river(surface, river, pixel_x, pixel_y)
                road = curr_hex.road
                if road != None:
                    images.draw_road(surface, road, pixel_x, pixel_y)
                
                if self.show_borders:
                    for direction in curr_hex.get_zone_borders():
                        images.draw_zone_border(surface, pixel_x, pixel_y, direction)
                
                site = curr_hex.site
                if site != None:
                    images.draw_site(site, surface, self.curr_mask.get_player(), (pixel_x, pixel_y))
                
                if visibility == mask.NOT_VISIBLE:
                    surface.blit(images.fogged_hex, (pixel_x, pixel_y))
                    continue
                
                image_x, image_y = pixel_x + 8, pixel_y + 8
                active_group = curr_hex.get_active_group()
                if active_group != None:
                    image_x, image_y = pixel_x + 8, pixel_y + 8
                    if active_group.get_move_mode() == move_mode.NAVAL:
                        group_image = images.boat
                    else:
                        group_image = images.unit_image(active_group.get_unit(0), True)
    
                    # if group is hidden, make it transparent if current viewer owns it, otherwise don't show it at all
                    if active_group.is_hidden():
                        images.blit_alpha(surface, group_image, (image_x, image_y), image.HIDDEN_TRANSPARENCY)
                    else:
                        surface.blit(group_image, (image_x, image_y))
                
                if active_group != None:
                    self.draw_unit_bar(surface, images, active_group, image_x, pixel_y, None)
                elif curr_hex.get_garrison() != None:
                    self.draw_unit_bar(surface, images, curr_hex.get_garrison(), image_x, pixel_y, curr_hex.site)
                
                if curr_hex.has_fire():
                    images.draw_animation(images.fire, pixel_x, pixel_y, surface)
                
                if curr_hex.has_storm():
                    images.draw_animation(images.storm, pixel_x, pixel_y, surface)
                
        if self.view.selected_hex != None:
            pixel_loc = self.view.pixel_from_hex(self.view.selected_hex.x, self.view.selected_hex.y)
            surface.blit(images.selected_hex, pixel_loc)
    
        for curr_hex in self.map_attack_event:
                pixel_loc = self.view.pixel_from_hex(curr_hex.x, curr_hex.y)
                surface.blit(images.combat_images[self.map_attack_event[curr_hex]], pixel_loc)
        
        if self.curr_player == self.curr_mask.get_player():
            for hex_loc in self.legal_moves:
                if self.curr_mask.get_visibility(hex_loc.x, hex_loc.y) != mask.NEVER_VISIBLE:
                    pixel_loc = self.view.pixel_from_hex(hex_loc.x, hex_loc.y)
                    if hex_loc.will_fight(self.curr_player):
                        surface.blit(images.attack_move, pixel_loc)
                    else:
                        surface.blit(images.legal_move, pixel_loc)
       
#    def render(self, surface, images):
#        render_map(surface, self.map_data, self.curr_mask, images, self.view)

        

                