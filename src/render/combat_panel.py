'''
Created on Jul 1, 2012

@author: Chris
'''
import  gamemap.mask as mask
from util.tools import Rect
import group_panel, text
import core.event_manager as event_manager
import gui.component as component
from gui.label import Label
import gui.modal as modal
import math, pygame

combat_event_types = [event_manager.COMBAT_START, event_manager.COMBAT_END, event_manager.COMBAT_UPDATE, event_manager.COMBAT_RETREAT, event_manager.COMBAT_SPOILS,
                      event_manager.RANGED_ATTACK, event_manager.HEAL_ATTEMPT,
                      event_manager.UNIT_HIT, event_manager.UNIT_HEAL, event_manager.UNIT_BLOCK]

phase_labels = {"Combat!": "", "Melee Combat" : "Strength: ", "Ranged Combat" : "Ranged: ", "Heal": "Heal: ", "Revive": "Revive: "}

class CombatRenderer(component.Window):
    '''
    classdocs
    '''

    def __init__(self, position_rect, images):
        global combat_event_types
        super(CombatRenderer, self).__init__(position_rect, True)
        
        self.mask = None
        self.active = False
        self.images = images
        self.phase = None
        
        attacker_rect = Rect(self.rect.x, self.rect.y + 30, self.rect.width, self.rect.height / 2 - 15)
        self.attacker_renderer = group_panel.CombatRenderer("Attackers:", attacker_rect)
        defender_rect = Rect(self.rect.x, attacker_rect.y + attacker_rect.height, self.rect.width, self.rect.height / 2 - 15)
        self.defender_renderer = group_panel.CombatRenderer("Defenders:", defender_rect)
    
        width, height = 120, 20
        x, y = self.rect.x + self.rect.width/2 - width/2, attacker_rect.y + attacker_rect.height - 20
        self.attacker_label = Label(Rect(x, y, width, height), None)
        y = defender_rect.y + defender_rect.height - 28
        self.defender_label = Label(Rect(x, y, width, height), None)
        
        self.add_child(self.attacker_renderer)
        self.add_child(self.defender_renderer)
        self.add_child(self.attacker_label)
        self.add_child(self.defender_label)
    
        event_manager.add_listener_multi(self.handle_game_events, combat_event_types)
    
    def set_data(self, map_renderer, curr_mask):
        self.mask = curr_mask
        self.map_renderer = map_renderer
    
    def handle_game_events(self, event):
        if event.type == event_manager.COMBAT_START:
            loc = event.data['hex_loc']
            if self.mask != None and self.mask.get_visibility(loc.x, loc.y) == mask.VISIBLE: 
                self.show()
                self.map_renderer.center(loc.x, loc.y) 
                self.attacker_renderer.set_group(event.data['attackers'])
                self.defender_renderer.set_group(event.data['defenders'])
                try:
                    self.attacker_renderer.set_label(event.data['attackers'].get_owner().name)
                    self.defender_renderer.set_label(event.data['defenders'].get_owner().name)
                except AttributeError:
                    self.hide()
                self.title_text = "Combat!"
                self.base_label = ""
#                
        elif self.is_shown() and event.type == event_manager.COMBAT_END:
            self.hide()
        elif self.is_shown() and event.type == event_manager.COMBAT_SPOILS:
            spoils_message = "For defeating this foe you earned \n"
            if event.data['reputation'] != 0:
                spoils_message +=  "\n    " + str(event.data['reputation']) + " Reputation"
            if event.data['item'] != None:
                spoils_message += "\n    " + event.data['item'].get_name()
            spoils_dialog = modal.TextDialog("Spoils", spoils_message)
            spoils_dialog.show()
        elif self.is_shown() and event.type == event_manager.COMBAT_RETREAT:
            self.title_text = "Retreat"
            retreat_text = "Retreat Chance: " + str(int(100 * event.data['retreat_chance'])) + "% , " + ("Retreated" if event.data['retreated'] else "Didn't Retreat")
            self.defender_label.set_label(retreat_text,  text_color=text.RED)
        elif self.is_shown():
            if event.type == event_manager.COMBAT_UPDATE:
                self.phase = event.data['phase'] 
                if self.phase != self.title_text:
                    self.title_text = event.data['phase']
                    self.base_label = phase_labels[self.title_text]
                
                attack_label_val = event.data['attacker_strength']
                defense_label_val  = event.data['defender_strength']
               
                if attack_label_val != None:
                    attack_label_color = text.RED if attack_label_val <= 0 else text.DARK
                    self.attacker_label.set_label(self.base_label + str(attack_label_val), text_color=attack_label_color)
                else:
                    self.attacker_label.set_label(None)
                if defense_label_val != None:
                    defense_label_color = text.RED if defense_label_val <= 0 else text.DARK
                    self.defender_label.set_label(self.base_label + str(defense_label_val), text_color=defense_label_color)
                else:
                    self.defender_label.set_label(None)
                
                self.attacker_renderer.mark_selected(event.data['attacker_index'])
                self.defender_renderer.mark_selected(event.data['defender_index'])  
#                self.attacker_renderer.add_overlay(self.images.selected_unit, event.data['attacker_index'])
#                self.defender_renderer.add_overlay(self.images.selected_unit, event.data['defender_index'])
                self.attacker_renderer.swap_overlays()
                self.defender_renderer.swap_overlays()
          
            else:
                affected_group = event.data['group']
                index = event.data['index']
                image = self.images.combat_images.get(event.type, None)
                if affected_group == self.attacker_renderer.curr_group:
                    self.attacker_renderer.add_overlay(image, index)
                else:
                    assert (affected_group == self.defender_renderer.curr_group)
                    self.defender_renderer.add_overlay(image, index)

    def set_mask(self, new_mask):
        self.mask = new_mask
    
    
    def render(self, surface, images):
        super(CombatRenderer, self).render(surface, images)

        x = self.rect.x + self.rect.width /2
        y = self.rect.y + text.vlg_font.get_height()
        images.text.draw_text(self.title_text, text.vlg_font, x, y, surface) 
        
        if self.phase != "Melee Combat" and self.phase != "Ranged Combat":
            return
        
        att_x, att_y = self.attacker_renderer.selected_anchor_point(True)
        def_x, def_y = self.defender_renderer.selected_anchor_point(False)
        if att_x == None or def_x == None:
            return
        
        dx = def_x - att_x 
        dy = def_y - att_y
        distance = int(math.hypot(dx, dy))
        line_width = images.fight_line.get_width()
        
        if self.phase == "Melee Combat":
            fight_line = images.fight_line  
        else:
            # ranged combat
            fight_line = images.shoot_line
            if self.attacker_label.get_label() == None:
                if self.defender_label.get_label() == None:
                    # no one actually shooting
                    return
                
                # defender is active, point arrow other way
                fight_line = pygame.transform.rotate(fight_line, 180)
        
        fight_line = pygame.transform.smoothscale(fight_line, (line_width, distance))
        
        
        if dx != 0:
            angle = math.degrees(math.atan(dy / float(dx)))
#            print "dx: " + str(dx) + " dy: " + str(dy) + " angle: " + str(angle)
            if angle < 0:
                angle = -90 - angle
            else:
                angle = 90 - angle
#            print "final angle: " + str(angle)
            fight_line = pygame.transform.rotate(fight_line, angle)
            
            if angle < 0:
                att_x -= fight_line.get_width() - line_width
                att_y += math.sin(math.radians(angle)) * (line_width / 2)
            else:
                att_y -= math.sin(math.radians(angle)) * (line_width/2)
            
        surface.blit(fight_line, (att_x - line_width / 2, att_y))

        