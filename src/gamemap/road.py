'''
Created on Feb 13, 2013

@author: Chris
'''
import hexgrid
from util.tools import Loc
from heapq import heappush, heappop

class Road(object):
    
    def __init__(self):
        self.connections = []
    
    def add_connection(self, dir):
        self.connections.append(dir)
    
# find all connected regions of the map that qualify for filter func.  Only use currently is
# for finding connected settled regions for purposes of making road nets, hence location of function
def find_regions(game_map, filter_func):
    region_to_locs = {}
    region_neighbors = {}
    loc_to_region = {}
    region_id = 0
    
    for y in range(game_map.height):
        for x in range(game_map.width):
            curr_hex = game_map.get_hex(x, y)
            if filter_func(curr_hex):
                curr_loc = Loc(x, y)
                region_to_locs[region_id] = [curr_loc]
                loc_to_region[curr_loc] = region_id
                region_neighbors[curr_loc] = []
                region_id +=1
              

    for loc in loc_to_region.iterkeys():
        neighbors = hexgrid.get_neighbor_coords(loc, game_map.width, game_map.height)
        region_id = loc_to_region[loc]
        for neighbor in neighbors:
            if neighbor in loc_to_region:
                region_neighbors[loc].append(neighbor)
                if loc_to_region[neighbor] != region_id:
                    
                    neighbor_id = loc_to_region[neighbor]
                    region_to_locs[region_id] += region_to_locs[neighbor_id]
                    for adj_region_loc in region_to_locs[neighbor_id]:
                        loc_to_region[adj_region_loc] = region_id
                    region_to_locs[neighbor_id] = []
    
    return [locs for locs in region_to_locs.values() if len(locs) > 0], region_neighbors

def find_settlements(region, game_map):
    settlement_locs = []
    
    for loc in region:
        loc_hex = game_map.get_hex(loc.x, loc.y)
        if loc_hex.has_site() and (loc_hex.site.settles() or loc_hex.site.is_haven()):  
            settlement_locs.append(loc)

    return settlement_locs        

def find_mst(region, sorted_edges, settlements):
    def filter_edges(sorted_edges):
        # clean up edges so it only contains visited - unvisited edges
        return 
    
    visited = {}
    for settlement in settlements:
        visited[settlement] = False
    
    visited[settlements[0]] = True
  
    mst_edges = []
    for i in range(1, len(settlements)):
        edge_index = 0
        while not (visited[sorted_edges[edge_index][0]] ^ visited[sorted_edges[edge_index][1]]): #not visited[sorted_edges[edge_index][0]] and not visited[sorted_edges[edge_index][1]]:
            edge_index += 1
        mst_edges.append(sorted_edges[edge_index])
#        # one of these was already True, but not worth the bother to find out which
        visited[sorted_edges[edge_index][0]] = True
        visited[sorted_edges[edge_index][1]] = True        
        
#        mst_edges.append(sorted_edges[0])
#        # one of these was already True, but not worth the bother to find out which
#        visited[sorted_edges[0][0]] = True
#        visited[sorted_edges[0][1]] = True        
        
        sorted_edges = [edge for edge in sorted_edges if not (visited[edge[0]] and visited[edge[1]])]
        #sorted_edges = [edge for edge in sorted_edges if visited[edge[0]] ^ visited[edge[1]]]
    
    return mst_edges

def find_road_path(region_neighbors, edge):
    reach_cost = {}
    predecessor = {}
    open_hexes = []
    closed_hexes = set([]) 

    reach_cost[edge[0]] = 0
    heappush(open_hexes, (hexgrid.get_distance(edge[0], edge[1]), edge[0]))
        
    while len(open_hexes) > 0:
        curr_cost, curr_loc = heappop(open_hexes)
        closed_hexes.add(curr_loc)
                
        # stop if we reach goal
        if curr_loc == edge[1]:
            break
    
        neighbors = region_neighbors[curr_loc]
                 
        for neighbor in neighbors:
            if neighbor in closed_hexes:
                continue
                
            new_cost = reach_cost[curr_loc] + 1
                      
            if (neighbor not in reach_cost) or (new_cost < reach_cost[neighbor]):
                reach_cost[neighbor] = new_cost
                predecessor[neighbor] = curr_loc
                heappush(open_hexes, (new_cost + hexgrid.get_distance(neighbor, edge[1]), neighbor)) 
        
        path = []
         
    assert (curr_loc == edge[1])
  
    while curr_loc != edge[0]:
        path.insert(0, curr_loc)
        curr_loc = predecessor[curr_loc]
    path.insert(0, edge[0])
    
#    if len(path) < hexgrid.get_distance(edge[0], edge[1]):
#        print "ERROR!"
#        print ("edge:" + str(edge))
#        print("path: " + str(path))
#        for loc in path:
#            print (str(loc) + " neighbors: " + str(region_neighbors[loc]))
    
    return path, reach_cost[edge[1]]

def find_road_paths(region_neighbors, edges):
    paths = {}

    for edge in edges:
        locs, path_cost = find_road_path(region_neighbors, edge)
        paths[edge] = {"cost": path_cost, "locs": locs}
    return paths

def build_road_net(game_map):
    regions, region_neighbors = find_regions(game_map, lambda x : x.is_settled())
    road_map = {}
    
    # clear existing roads
    for y in range(game_map.height):
        for x in range(game_map.width):
            game_map.get_hex(x, y).set_road(None)    
#    road_msts = []
    for region in regions:
        settlements = find_settlements(region, game_map)
        if len(settlements) <= 1:
            continue
        
        edges = []
        for i in range(len(settlements)):
            for j in range(i + 1, len(settlements)):
                edges.append( (settlements[i], settlements[j]) )
    
        paths = find_road_paths(region_neighbors, edges)
        edges.sort(key = lambda edge: paths[edge]["cost"])
            
        road_mst = find_mst(region, edges, settlements)
#        print("settlements: " + str(settlements))
#        print("Mst: " + str(road_mst))
        for edge in road_mst:
#            print ("edge: " + str(edge) + " path: " + str(paths[edge]["locs"]))
            for loc in paths[edge]["locs"]:
                road_map[loc] = True
#               game_map.get_hex(loc.x, loc.y).set_road()
    
    for loc in road_map.iterkeys():        
        hex_road = Road()
        neighbors = hexgrid.get_neighbor_coords(loc, game_map.width, game_map.height)
        for neighbor in neighbors:
            if neighbor in road_map:
                hex_road.add_connection(hexgrid.get_direction(loc, neighbor))
        game_map.get_hex(loc.x, loc.y).set_road(hex_road)