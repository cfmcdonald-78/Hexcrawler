'''
Created on Jun 29, 2012

@author: Chris
'''
import pygame, os
import gamemap.terrain as terrain, gamemap.site_type as site_type, mob.unit as unit, gamemap.hexgrid as hexgrid, mob.item as item
from util.tools import make_2D_list
import core.event_manager as event_manager
import text

MAX_FRAME = 2
TICKS_PER_FRAME = 10

UNIT_WIDTH = 64
UNIT_HEIGHT = 64
MAP_UNIT_WIDTH = 48
MAP_UNIT_HEIGHT = 48
ITEM_ICON_WIDTH = 48
ITEM_ICON_HEIGHT = 48
HEX_WIDTH = 54 
HEX_HEIGHT = 64 
UI_ICON_WIDTH = 32
UI_ICON_HEIGHT = 32
SM_BUTTON_WIDTH = 24
SM_BUTTON_HEIGHT = 24
CONTROL_BUTTON_WIDTH = 32
CONTROL_BUTTON_HEIGHT = 32
PLAYER_SUB_COLOR = (255, 0, 255)

NORMAL_WATER_COLOR1 = (45, 84, 153)
NORMAL_WATER_COLOR2 = (94, 105, 241)
FLOODED_WATER_COLOR1 = ( 114, 105, 96)
FLOODED_WATER_COLOR2 = (203, 187, 171)

HIDDEN_TRANSPARENCY = 128

class ImageManager(object):
    
    def __init__(self, font_file):
        self.unit_images = {}
        self.unit_map_images = {}
        for unit_type in unit.unit_types:
            self.unit_images[unit_type.name] = self.prep_image("unit", unit_type.name + ".png")
            self.unit_map_images[unit_type.name] = self.prep_image("unit", unit_type.name + ".png", (MAP_UNIT_WIDTH, MAP_UNIT_HEIGHT))

        self.boat = self.prep_image("unit", "boat.png", (MAP_UNIT_WIDTH, MAP_UNIT_HEIGHT))
        
        self.site_images = {}
        self.sacked_images = {}
        for image_site_type in site_type.site_types.values(): 
            self.site_images[image_site_type.name] = self.prep_image("map", image_site_type.name + ".png")
            if image_site_type.loot_effects != None and (image_site_type.loot_effects.new_status == site_type.SACKED or
                                                         image_site_type.loot_effects.new_status == site_type.ACTIVE):
                self.sacked_images[image_site_type.name] = self.prep_image("map", "sacked " + image_site_type.name + ".png")
        
#        self.upgrade_images = {}
#        for upgrade_name in site_upgrade.upgrades_by_name:
#            self.upgrade_images[upgrade_name] = self.prep_image("map", upgrade_name + ".png")
#        
        self.hex_images = {}
        for terrain_type in terrain.hex_types:
            self.hex_images[terrain_type.name] = self.prep_image("map", terrain_type.name + ".png")
    
        self.river = {}    
        for angle in range(0, 4):
            self.river[angle] = self.prep_image("map", "river" + str(angle) + ".png")
        self.river[(2,1)] = self.prep_image("map", "river21.png")
        self.river[(3,1)] = pygame.transform.flip(self.river[(2,1)], False, True) # self.prep_image("map", "river21.png")
        self.river[(2,2)] = self.prep_image("map", "river22.png")
        self.river_frag = self.prep_image("map", "river frag.png")
        
        self.zone_border = self.prep_image("map", "zone_border.png")
        
        self.storm = self.prep_animation("map", "storm")
        self.fire = self.prep_animation("map", "fire")
    
        self.selected_hex = self.prep_image("ui", "selected_hex.png")
        self.legal_move = self.prep_image("ui", "legal_move.png")
        self.attack_move = self.prep_image("ui", "attack_move.png")
        self.selected_unit = self.prep_image("ui", "selected_unit.png")
        self.selected_item = self.prep_image("ui", "selected_item.png")
        self.dead_image = self.prep_image("ui", "dead.png")
        
        self.unit_slot = self.prep_image("ui", "unit_slot.png")
        
        self.combat_images = {}
        self.wounded_image = self.prep_image("ui", "wounded.png")
        self.restrained_image = self.prep_image("ui", "restrained.png")
        self.burning_image = self.prep_image("ui", "burning.png")
        self.combat_images[event_manager.UNIT_HIT] = self.prep_image("ui", "hit.png")
        self.combat_images[event_manager.UNIT_BLOCK] = self.prep_image("ui", "block.png")
        self.combat_images[event_manager.RANGED_ATTACK] = self.prep_image("ui", "ranged.png")
        self.combat_images[event_manager.HEAL_ATTEMPT] = self.prep_image("ui", "magic.png")
        #self.combat_images[combat.HEALED] = self.prep_image("heal.png")
        self.combat_images[event_manager.UNIT_HEAL] = self.prep_image("ui", "heal.png")
       
        self.equip_slots = {}
        self.item_icons = {}
        for item_type in item.item_types:
            self.item_icons[item_type] = self.prep_image("item", item_type + ".png")
            self.equip_slots[item_type] = self.prep_image("item", item_type + "_slot.png")
        self.backpack_slot = self.prep_image("item", "backpack_slot.png")
        
        self.banner = self.prep_image("ui", "banner.png")
        self.fogged_hex = self.prep_image("ui", "fogged_hex.png")
        self.invisible_hex = self.prep_image("ui", "invisible_hex.png")
        self.l_arrow = self.prep_image("ui", "l_arrow.png")
        self.r_arrow = self.prep_image("ui", "r_arrow.png")
        self.transfer = self.prep_image("ui", "transfer.png")
        self.disband = self.prep_image("ui", "disband.png")
        self.prev_site = self.prep_image("ui", "prev_site.png")
        self.next_site = self.prep_image("ui", "next_site.png")
        self.center_view = self.prep_image("ui", "center_view.png")
        self.end_turn = self.prep_image("ui", "end_turn.png")
        self.tools = self.prep_image("ui", "tools.png")
        self.gold = self.prep_image("ui", "gold.png")
        self.gold_small = self.prep_image("ui", "gold_24.png")
        self.chains = self.prep_image("ui", "chains.png")
        self.reputation = self.prep_image("ui", "reputation.png")
        self.fame = self.prep_image("ui", "fame.png")
        self.income = self.prep_image("ui", "income.png")
        self.revolt = self.prep_image("ui", "revolt.png")
        self.embassy = self.prep_image("ui", "embassy.png")
        self.exhaustion = self.prep_image("ui", "exhaustion.png")
        self.supply = self.prep_image("ui", "supply.png")
        self.blood = self.prep_image("ui", "blood.png")
        self.inspire = self.prep_image("ui", "inspire.png")
        self.foot_move = self.prep_image("ui", "foot_move.png")
        self.naval_move = self.prep_image("ui", "naval_move.png")
        self.strength = self.prep_image("ui", "strength.png")
        self.armor = self.prep_image("ui", "armor.png")
        self.looting = self.prep_image("ui", "looting.png")
        self.window_9patch = self.prep_9patch("ui", "window_9patch.png")
        self.region_9patch = self.prep_9patch("ui", "region_9patch.png")
        self.button_9patch = self.prep_9patch("ui", "button_9patch.png")
        self.button_down_9patch = self.prep_9patch("ui", "button_down_9patch.png")
        self.fight_line = self.prep_image("ui", "fight_line.png")
        self.shoot_line = self.prep_image("ui", "shoot_line.png")
        #self.icon = self.prep_image("icon.png")
        self.text = text.TextDrawer(font_file)
        self.PAD = 2
        
        self.temp_surfaces = {}
        self.temp_surfaces[(MAP_UNIT_WIDTH, MAP_UNIT_HEIGHT)] = pygame.Surface((MAP_UNIT_WIDTH, MAP_UNIT_HEIGHT)).convert()
        
#        self.initialize()
    
    def blit_alpha(self, target, source, location, opacity):
        x, y = location
        temp = self.temp_surfaces[(source.get_width(), source.get_height())] 
        temp.blit(target, (-x, -y))
        temp.blit(source, (0, 0))
        temp.set_alpha(opacity)        
        target.blit(temp, location)
    
    def initialize(self):
        event_manager.add_listener(self.handle_game_events, event_manager.TICK)
    
        self.frame_num = 0
        self.frame_inc = 1
        self.tick_count = 0

    def handle_game_events(self, event):
        if event.type == event_manager.TICK:
            if self.tick_count < TICKS_PER_FRAME:
                self.tick_count += 1
                return
            self.tick_count = 0
            if self.frame_num == MAX_FRAME:
                self.frame_inc = -1
            elif self.frame_num == 0:
                self.frame_inc = 1
            self.frame_num += self.frame_inc 
    
    def draw_window(self, surface, rect):
        self.draw_9patch(surface, self.window_9patch, rect)
    
    def draw_button(self, surface, rect, down):
        if down:
            self.draw_9patch(surface, self.button_down_9patch, rect)
        else:
            self.draw_9patch(surface, self.button_9patch, rect)
    
    def draw_textbox(self, surface, rect, text_value, has_focus):
#        self.draw_9patch(surface, self.textbox_9patch, rect)
        if has_focus: 
            surface.fill((230, 230, 230), rect = rect)
        else:
            surface.fill((170, 170, 170), rect = rect)
        
        self.text.draw_text(text_value, text.lg_font, rect.x + 4, rect.y + 4, surface, centered=False)
        
        
    def draw_9patch(self, surface, (patch_size, nine_patch), rect):
        x_scale, y_scale = False, False
        if rect.width > patch_size * 3:
            x_scale = True
        if rect.height > patch_size * 3 :
            y_scale = True
#            raise ValueError("can't shrink 9 patch image")   
        
        x_pos = [rect.x, rect.x + patch_size, 
                 rect.x + rect.width - patch_size, rect.x + rect.width]
        y_pos = [rect.y, rect.y + patch_size, 
                 rect.y + rect.height - patch_size, rect.y + rect.height]
        for y in range(3):
            if rect.height <= patch_size * 2 and y == 1:
                continue
            for x in range(3):
                scaled = pygame.transform.scale(nine_patch[x][y], 
                                                ((x_pos[x + 1] - x_pos[x]) if x_scale else patch_size, 
                                                 (y_pos[y + 1] - y_pos[y]) if y_scale else patch_size))
                surface.blit(scaled, (x_pos[x], y_pos[y]))
        
    def draw_site(self, site, surface, mask_player, position):
        if site.sacked():
            site_image = self.sacked_images[site.site_type.name]
            surface.blit(site_image, position)
        else:
            site_image = self.site_images[site.site_type.name]
            site_pixels = pygame.PixelArray(site_image)
                        
            # swap in owner color for flags and the like on the site, to indicate ownership
            owner_color = site.owner.get_color(site, mask_player)
            site_pixels.replace(PLAYER_SUB_COLOR, owner_color)
            del site_pixels # unlock image so pygame can draw it
            surface.blit(site_image, position)            
             # swap color back
            site_pixels = pygame.PixelArray(site_image)
            site_pixels.replace(owner_color, PLAYER_SUB_COLOR)
            del site_pixels 
            
            if site.get_fixed_prisoner() != None:
                x, y = position
                surface.blit(self.chains, (x + 8, y + 8))
            
            if site.get_embassy() != None:
                x, y = position
                embassy_pixels = pygame.PixelArray(self.embassy)
                owner_color = site.get_embassy().get_color(site, mask_player)
                embassy_pixels.replace(PLAYER_SUB_COLOR, owner_color)
                del embassy_pixels # unlock image so pygame can draw it
                surface.blit(self.embassy, (x + 8, y + 8))           
             # swap color back
                embassy_pixels = pygame.PixelArray(self.embassy)
                embassy_pixels.replace(owner_color, PLAYER_SUB_COLOR)
                
            
            # draw upgrade images
#            for upgrade_name in site.get_upgrades():
#                surface.blit(self.upgrade_images[upgrade_name], position)
    
    
    def pos_from_dir(self, x, y, direction):
        if direction == hexgrid.WEST:
            dx, dy = 6, 32
        if direction == hexgrid.EAST:
            dx, dy = 58, 32
        if direction == hexgrid.NORTHEAST:
            dx, dy = 46, 8
        if direction == hexgrid.NORTHWEST:
            dx, dy = 18, 8
        if direction == hexgrid.SOUTHEAST:
            dx, dy = 46, 56
        if direction == hexgrid.SOUTHWEST:
            dx, dy = 18, 56
        
        return (x + dx , y + dy)
    
    
    def draw_zone_border(self, surface, pixel_x, pixel_y, direction):
        angle = direction * -60
        
        if angle % 90 != 0:
            pixel_x -= 12
            pixel_y -= 13
        
        image = pygame.transform.rotate(self.zone_border, angle)  
        surface.blit(image, (pixel_x, pixel_y))
    
    def draw_river_image(self, surface, image, angle, pixel_x, pixel_y, flooded):
        if angle % 90 != 0:
            pixel_x -= 12
            pixel_y -= 12
        
        image = pygame.transform.rotate(image, angle)    
        
        if flooded:
            river_pixels = pygame.PixelArray(image)
                        
            # swap in owner color for flags and the like on the site, to indicate ownership
#            owner_color = site.owner.get_color(site.level, mask_player)
            river_pixels.replace(NORMAL_WATER_COLOR1, FLOODED_WATER_COLOR1)
            river_pixels.replace(NORMAL_WATER_COLOR2, FLOODED_WATER_COLOR2)
            del river_pixels # unlock image so pygame can draw it
        
        surface.blit(image, (pixel_x, pixel_y))
        
    
    def draw_river(self, surface, river, pixel_x, pixel_y):
        in_flows, out_flow = river.in_flows, river.out_flow
        
        image = None
        if len(in_flows) == 0:
            image = self.river[0]
            angle = -60 * out_flow
        elif len(in_flows) == 1: 
            abs_angle =   hexgrid.get_abs_angle(in_flows[0], out_flow)
            image = self.river[abs_angle]
            if abs(in_flows[0] - out_flow) > abs_angle:
                angle = -60 * max(in_flows[0], out_flow)
            else:
                angle = -60 * min(in_flows[0], out_flow)
        elif len(in_flows) == 2:
            angle_ins = hexgrid.get_clock_angle(in_flows[0], in_flows[1])# hexgrid.get_abs_angle(in_flows[0], in_flows[1])
            angle_out = hexgrid.get_clock_angle(out_flow, in_flows[0]) #hexgrid.get_abs_angle(in_flows[0], out_flow)
            image = self.river.get((angle_out, angle_ins), None)
            angle = -60 * (out_flow - hexgrid.WEST)
        
        if image == None: # patch together something that looks okay
            for in_flow in in_flows:
                angle = -60 * (in_flow - hexgrid.WEST)
                self.draw_river_image(surface, self.river_frag, angle, pixel_x, pixel_y, river.is_flooded)    
            angle = -60 * (out_flow - hexgrid.WEST)  
            self.draw_river_image(surface, self.river_frag, angle, pixel_x, pixel_y, river.is_flooded)   
            return
       
        self.draw_river_image(surface, image, angle, pixel_x, pixel_y, river.is_flooded)

    def prep_animation(self, sub_dir, base_file_name):
        animation = []
        for i in range(MAX_FRAME + 1):
            animation.append(self.prep_image(sub_dir, base_file_name + str(i) + ".png"))
        return animation
    
    def prep_9patch(self, sub_dir, image_file_name):
        nine_patch = make_2D_list(3, 3, None)
        base_image = self.prep_image(sub_dir, image_file_name)
        patch_size = base_image.get_width() / 3
        assert(base_image.get_width() == base_image.get_height())
        
        for y in range(3):
            for x in range(3):
                nine_patch[x][y] = base_image.subsurface((x * patch_size, y * patch_size, 
                                                          patch_size, patch_size)).copy()
        return patch_size, nine_patch
    
    def prep_image(self, sub_dir, image_file_name, rescale = None):
        try:
            # TODO: replace direct file access with packaged resources (setup.py)
            image = pygame.image.load(os.path.join('data', 'img', sub_dir, image_file_name))
            if rescale != None:
                image = pygame.transform.smoothscale(image, rescale)
        except pygame.error, message:
            print 'Cannot load image:', image_file_name
            raise SystemExit, message
        return image.convert_alpha()

    def draw_animation(self, animation, pixel_x, pixel_y, surface):
        surface.blit(animation[self.frame_num], (pixel_x, pixel_y))

    def unit_image(self, unit, on_map = False):
        if on_map:
            return self.unit_map_images[unit.type_name]
        else:
            return self.unit_images[unit.type_name]

    def hex_image(self, terrain):
        return self.hex_images[terrain.name]
