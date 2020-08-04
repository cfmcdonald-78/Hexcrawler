'''
Created on Jul 17, 2012

@author: Chris
'''
import shelve, dbhash, anydbm
import os.path
import core.options as options

#class SaveCommand(command.Command):
#    
#    def __init__(self, game, view, save_file):
#        self.game = game
#        self.view = view
#        self.save_file = save_file
#    
#    def validate(self):
#        #TODO: validation
#        return True
#    
#    def execute(self):
        
        
#class LoadGame(activity.Activity):
#    
#    def __init__(self, game, save_file):
#        self.game = game
#        self.save_file = save_file
#        self.default_delay = activity.FILE_IO_DELAY
#    
#    def get_curr_hex(self):
#        return None
#    
#    def do_next(self):
#        save_file = shelve.open(self.save_file)
#        self.game = save_file['game_data']
#        save_file.close()
##       
#        return FILE_OPERATION_DONE

def save_game(game, view):
    save_file = shelve.open("save_game")
    save_file['game_data'] = game
    save_file['view'] = view
    save_file.close()

   # game.handle_command(SaveCommand(game, view, "save_game"))
 #   game.wait_for_activities()

def can_load(file_name):
    return os.path.isfile(file_name)

def can_load_game():
    return can_load('save_game')

def load_game():
    save_file = shelve.open("save_game")
    loaded_game = save_file['game_data']
    loaded_view = save_file['view']
    save_file.close()
    return loaded_game, loaded_view
#    game.queue_activity(LoadGame("save_game"))
#    game.wait_for_activities(self):
#        self.activities_finished.wait()


def save_options():
    options_file = shelve.open("options")
    options_file['options_data'] = options.curr_options
    options_file.close()

def load_options():
    if can_load('options'):
        options_file = shelve.open("options")
        return options_file['options_data']
    else:
        # no option file found, create new options object
        return options.Options()