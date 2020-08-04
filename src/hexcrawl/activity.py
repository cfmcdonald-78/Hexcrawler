'''
Created on Jul 2, 2012

@author: Chris
'''
# frequency of updates in millisecs
HIDDEN_DELAY = 0
AI_SPEEDUP = 5
DEFAULT_DELAY = 500


FILE_IO_DELAY = 0

#class Command(object):
#    pass
#
#class ActivityResult(object):
#    
#    def __init__(self, value):
#        self.value = value
#
#ACTIVITY_DONE = ActivityResult("ACTIVITY_DONE")
#
#class Activity(object):
#    '''
#    classdocs
#    '''
#
#
#    def __init__(self, is_ai):
#        '''
#        Constructor
#        '''
#        self.is_ai_activity = is_ai
#        self.default_delay = DEFAULT_DELAY
#    
#    def update_delay(self, visibile):
#        if not visibile:
#            return HIDDEN_DELAY
#        if self.is_ai_activity:
#            return self.default_delay / AI_SPEEDUP
#        return self.default_delay
        