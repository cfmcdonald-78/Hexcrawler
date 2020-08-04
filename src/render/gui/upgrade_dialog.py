'''
Created on Sep 1, 2012

@author: Chris
'''
from modal import ModalDialog
import render.image as image
import component
from button import Button
from label import Label
import gamemap.site_upgrade as site_upgrade
from util.tools import Rect
from hexcrawl.misc_commands import UpgradeCommand
from core.event_manager import Event
import core.event_manager as event_manager
import render.text as text

class UpgradeDialog(ModalDialog):
    
    def __init__(self, width, height, head_text, updgrade_site):
        super(UpgradeDialog, self).__init__(width, height, head_text)
        self.site = updgrade_site
        
        self.temp_children = []
        self.update_upgrades()
        event_manager.add_listener(self.handle_game_events, event_manager.SITE_UPGRADED)
        
#        x = self.rect.x + self.rect.width / 8
#        y = self.rect.y + self.rect.height / 5
#        label_width = 125
#        button_width = 60
#        label_height = 20
#        for upgrade in self.available_upgrades:
#            # TODO: create upgrade command here and embed it in lambda callback, which will try to execute it 
#            self.add_child(Label(Rect(x, y, label_width, label_height), upgrade.name))
#            self.add_child(Button(Rect(x + label_width + 4, y, button_width, label_height), str(upgrade.cost), upgrade_callback))
#            y += label_height + 4
#            self.add_child(Button(Rect(x, y, width, height), "Sell", sell_callback))

    def handle_game_events(self, event):
        if event.type == event_manager.SITE_UPGRADED:
            self.update_upgrades()
    
    def close_window(self):
        event_manager.remove_listener(self.handle_game_events, event_manager.SITE_UPGRADED)
        super(UpgradeDialog, self).close_window()
    
    def do_upgrade(self, upgrade_name):
        upgrade_command = UpgradeCommand(self.site, upgrade_name)
        event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [upgrade_command]))
    
    def update_upgrades(self):
        
        for child in self.temp_children:
            self.remove_child(child)
        
        self.temp_children = []
        y = self.rect.y + self.rect.height / 8
        label_height = 20
        
        self.temp_children.append(Label(Rect(self.rect.x, y, self.rect.width, label_height), "Current Upgrades", font=text.lg_font) )  
        y += label_height + 4
        for upgrade in self.site.get_upgrades():
            tt_text = site_upgrade.upgrades_by_name[upgrade].description
            self.temp_children.append(Label(Rect(self.rect.x, y, self.rect.width, label_height), 
                                            upgrade, tool_tip_text=tt_text) )  
            y += label_height + 4
            
        y += 8
        
        x = self.rect.x + self.rect.width / 8
        label_width = self.rect.width / 2
        button_width = 60
     
        
        self.temp_children.append(Label(Rect(self.rect.x, y, self.rect.width, 20), "Available Upgrades", font=text.lg_font) )  
        y += label_height + 4
        avail_upgrades = site_upgrade.available_upgrades(self.site)
        
        upgrade_callbacks = [lambda upgrade_i=upgrade: self.do_upgrade(upgrade_i.name) for upgrade in avail_upgrades]
        
        for i in range(len(avail_upgrades)):
            tt_text = avail_upgrades[i].description
            self.temp_children.append(Label(Rect(x, y, label_width, label_height),
                                             avail_upgrades[i].name, tool_tip_text=tt_text) )  
            self.temp_children.append(Button(Rect(x + label_width + 4, y, button_width, label_height), 
                                             str(avail_upgrades[i].get_cost(self.site)), upgrade_callbacks[i]) )
             
            y += label_height + 4
    
        for child in self.temp_children:
            self.add_child(child)
            child.show()
#        if self.selected_item == None:
#            return
#        command =  misc_commands.ItemSellCommand(self.unit, self.selected_item[0] == 1, self.selected_item[1])
#        event_manager.queue_event(Event(event_manager.COMMAND_ISSUED, [command]))
    
    def event_handler(self, event):
 
        return super(UpgradeDialog, self).event_handler(event)