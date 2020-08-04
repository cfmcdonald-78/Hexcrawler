'''
Created on Jun 27, 2012

@author: Chris
'''
import hexgrid

MAX_INFLOWS = 2

class River(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.in_flows = []
        self.out_flow = None
        self.is_flooded = False
    
    def add_inflow(self, direction):
        assert (self.num_inflows() < MAX_INFLOWS)
        if direction not in self.in_flows:
            self.in_flows.append(direction)
        # sort in flows in clockwise order from out flow
        self.in_flows.sort(key = lambda in_flow : hexgrid.get_clock_angle(self.out_flow, in_flow)) #(in_flow - self.out_flow) % 6)
            
    def set_outflow(self, direction):
        self.out_flow = direction
    
    def num_inflows(self):
        return len(self.in_flows)
        
    def flood(self, days):
        self.is_flooded = True
        self.flood_duration = days
    
    # called by map each time a day passes
    def update_flood_state(self):
        if self.is_flooded:
            self.flood_duration -= 1
            if self.flood_duration == 0:
                self.is_flooded = False
 
    def is_flooded(self):
        return self.is_flooded