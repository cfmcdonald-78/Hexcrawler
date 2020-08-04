'''
Created on Jun 26, 2012

@author: Chris
'''
import sys
from collections import deque, namedtuple 

if __name__ == '__main__':
    pass

BIGNUM = sys.maxsize

Loc = namedtuple('Loc', ['x', 'y'])
Rect = namedtuple('Rect', ['x', 'y', 'width', 'height'])

def breadth_first_search(start, max_cost, neighbor_func, cost_func, exclude_start=False):
        to_visit = deque()
        to_visit.appendleft((0, start))
        visited = set([])
        while len(to_visit) > 0:
            cost, visiting = to_visit.pop()
            for neighbor in neighbor_func(visiting):
                if neighbor in visited:
                    continue
                reach_cost = cost + cost_func(visiting, neighbor)
                if reach_cost <= max_cost:
                    to_visit.appendleft((reach_cost, neighbor))
            
            visited.add(visiting)
        if exclude_start:
            visited.remove(start)
        return visited

def inside(rect, x, y):
    return x >= rect.x and y >= rect.y and x < (rect.x + rect.width) and y < (rect.y + rect.height)

def make_2D_list(width, height, init_value = None):
    new_list = []
    for x in range(width):
        new_list.append([])
        for y in range(height):
            new_list[x].append(init_value)
    return new_list

def min_in_list(data, min_func):
        smallest = None
        smallest_val = BIGNUM
        for element in data:
            elem_val = min_func(element)
            if  elem_val < smallest_val:
                smallest = element
                smallest_val = elem_val
        
        return smallest, smallest_val

def max_in_list(data, max_func):
        biggest = None
        biggest_val = -BIGNUM
        for element in data:
            elem_val = max_func(element)
            if  elem_val > biggest_val:
                biggest = element
                biggest_val = elem_val
        
        return biggest, biggest_val

def linked_list_insert(item_list, new_item):
        if len(item_list) > 0:
            last_item = item_list[-1]
            last_item.set_next(new_item)
            first_item = item_list[0]
            first_item.set_previous(new_item)
        else:
            last_item = new_item
            first_item = new_item
        
        new_item.set_previous(last_item)
        new_item.set_next(first_item)

def linked_list_remove(item_list, old_item):
    remove_index = item_list.index(old_item)
        
    if len(item_list) > 1:
            # if this isn't last item being removed, fix linked list pointers
            prev_item = item_list[remove_index - 1] # always works because -1 means end of list in Python
            next_item = item_list[(remove_index + 1) % len(item_list)]
            prev_item.set_next(next_item)
            next_item.set_previous(prev_item)

class DoublyLinkedObject(object):
    
    def __init__(self):
        self.next = self.previous = None
    
    # extreme recursion depth caused by circular list, so delete list pointers when getting state for save.
    def __getstate__(self):
        d = dict(self.__dict__)
        if 'next' in d:
            del d['next']
            del d['previous']
        return d
    
    def get_next(self):
        return self.next
    
    def get_previous(self):
        return self.previous
    
    def set_next(self, next_item):
        self.next = next_item
        
    def set_previous(self, previous_item):
        self.previous = previous_item
        
    
    