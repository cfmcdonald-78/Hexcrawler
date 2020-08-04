'''
Created on Jul 13, 2012

@author: Chris
'''
from collections import namedtuple
import event_manager 
import threading

ProcessType = namedtuple('ProcessType', ['name', 'data_values'])
# combat
# loot
# move
# delay

#LootType

UNINITIALIZED = 0
RUNNING = 1
PAUSED = 2
SUCCEEDED = 3
FAILED = 4
ABORTED = 5

process_mgr_lock = threading.Lock()
activities_finished = threading.Event()

activities_finished.set()

class Process(object):
    
    def __init__(self):
        self.state = UNINITIALIZED
        self.child = None
        
    def get_state(self):
        return self.state
    
    def is_alive(self):
        return self.state == RUNNING or self.state == PAUSED
    def is_dead(self):
        return self.state == SUCCEEDED or self.state == FAILED or self.state == ABORTED
    def is_running(self):
        return self.state == RUNNING

    def init(self):
        self.state = RUNNING
    
    def abort(self):
        self.state = ABORTED
        self.on_abort()
    
    def succeed(self):
        self.state = SUCCEEDED
    
    def fail(self):
        self.state = FAILED
        
    def on_fail(self):
        pass
    
    def on_success(self):
        pass
    
    def on_abort(self):
        pass
    def pause(self):
        if self.state == RUNNING:
            self.state = PAUSED
        else:
            print self.state
            raise ValueError("tried to pause non-running process")
        
    def unpause(self):
        if self.state == PAUSED:
            self.state = RUNNING
        else:
            raise ValueError("tried to resume non-paused process")
        
    def get_child(self):
        return self.child
    
    def attach_child(self, child_process):
        self.child = child_process

class StepProcess(Process):
    
    def __init__(self, delay_time, human_visible):
        super(StepProcess, self).__init__()
        self.wait_time = delay_time if human_visible else 0
        self.human_visible = human_visible
        self.accumulated_delay = self.wait_time # trigger immediate update, only wait on later updates
    
    def next_step(self):
        pass
    
    # TODO: event handling method  that suppresses events for non-human visible events
       
    def on_update(self, delta_ms):
        self.accumulated_delay += delta_ms
        if self.accumulated_delay < self.wait_time:
            return
        
        self.accumulated_delay = 0
        
        if self.wait_time == 0: 
            while self.is_running():
#                print "in update loop for process " + str(self)
                self.next_step()
        else:
            # do one step, then wait next update (and elapse of delay time)
            self.next_step()



class DelayProcess(Process):
    
    def __init__(self, time_to_delay):
        self.state = UNINITIALIZED
        self.time_do_delay = time_to_delay
        self.delayed_so_far = 0
        
    def on_update(self, delta_ms):
        self.delayed_so_far += delta_ms
        if self.delayed_so_far >= self.time_do_delay:
            self.succeed()

class DelayedEventProcess(DelayProcess):

    def __init__(self, time_to_delay, event):
        super(DelayedEventProcess, self).__init__(time_to_delay)
        self.event = event
    
    def on_success(self):
        super(DelayedEventProcess, self).on_success()
        event_manager.queue_event(self.event)

process_list = []



def update_processes(delta_ms):
    global process_list, activities_finished
    global UNINITIALIZED, RUNNING, SUCCEEDED, FAILED, ABORTED
    success_count, fail_count = 0, 0
    
    i = 0
    get_activity_lock()
    while i < len(process_list):
        process = process_list[i]
#        print "updating process " + str(process) 
#        if hasattr(process, 'group'):
#            print "group: " + str(process.group)
#        if hasattr(process, 'get_curr_hex'):
#            print "hex: " + str(process.get_curr_hex())
        if process.get_state() == UNINITIALIZED:
            process.init()
        if process.get_state() == RUNNING:
            process.on_update(delta_ms)
            
        if process.is_dead():
            dead_state = process.get_state()
            if dead_state == SUCCEEDED:
                process.on_success()
                child = process.get_child()
                if child != None:
                    attach_process(child)
                else:
                    success_count += 1 # only count completed chain, not every link
            elif dead_state == FAILED:
                process.on_fail()
                fail_count += 1
            elif dead_state == ABORTED:
                process.on_abort()
                fail_count += 1
            process_list = process_list[:i] + process_list[i+1:]
        else:
            i += 1       
    
#    print "acquiring lock to update" + " from " + str(threading.current_thread())
#    process_mgr_lock.acquire()
#    print "update lock acquired" + " from " + str(threading.current_thread())
    if len(process_list) == 0:
        activities_finished.set()
#        
#    print "releasing update lock" + " from " + str(threading.current_thread())
#    process_mgr_lock.release()
    release_activity_lock()
    return success_count, fail_count            


def get_activity_lock():
    process_mgr_lock.acquire()

def release_activity_lock():
    process_mgr_lock.release()
 
def wait_for_quiet():
    global activities_finished
    activities_finished.wait()

def attach_process(process):
    global process_list, activities_finished
    activities_finished.clear()
    process_list.append(process)

def abort_all_processes():
    global process_list
    process_list = []

def get_process_count():
    global process_list
    return len(process_list)
