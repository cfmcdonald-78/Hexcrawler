'''
Created on Jan 5, 2013

@author: Chris
'''
import random

def gen_name(name_maker, used_names, forced_pattern=None):
    if name_maker == None:
        return ""
    prefix = name_maker["prefix"]
    delimiter = name_maker["delimiter"]
    if forced_pattern == None:
        pattern = random.choice(name_maker["patterns"])
    else:
        pattern = name_maker["patterns"][forced_pattern]
    components = name_maker["components"]
        
    while True:
        name = prefix 
        for i in range(len(pattern)):
            percentage = pattern[i]
            if random.randint(1, 100) <= percentage:
                name += delimiter + random.choice(components[i])
        if name not in used_names:
            break
        
    used_names[name] = True
        
    return name
    