## Overview
I created this game in 2012-2013 using Python 2.7 and Pygame to try out procedural generation of terrain, rivers, road nets, monster lairs, etc. The (very bad) art and sound effects are my own.

Unfortunately it was more fun to build than it is to play :-) 

The most interesting files are:
* [src/gamemap/hexmap.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/hexmap.py) (Code for handling all the different states of a map location)
* [src/gamemap/map_maker.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/map_maker.py) (Code for generating the map before the start of the game).
* [src/gamemap/road.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/road.py) (Code for generating a road net between settlements)

Among other things you can:
* Recruit new units and heroes at settlements
* Conquer settlements, or befriend them with diplomats
* Defeat lairs full of monsters
* Find treasures and equip them onto your heroes
* Enter ever more dangerous territories in search of more dangerous monsters and more powerful units and treasures

The game engine can produce a variety of events each day including:
* Floods near rivers
* Forest fires
* Re-wilding of areas around destroyed settlements
* Fights between the patrols of order and chaos
* Large invading armies 

All the game data (types of monsters, treasure, sites, map zones, etc.) is defined in JSON. 

## Procedural Generation

### Terrain
1. A diamond-square algorithm is used to create a heightmap value for each hex.
1. A random set of river sources is created on high ground. These flow downhill until they reach level 0 (sea), another river, or the edge of the map. They can erode their way through terrain to avoid being trapped in local minima. 
1. Forests are generated on the low ground randomly with diamond-square, with a greater probability of forming next to a river, and a lower probability of forming next to a mountain.
1. Each other hex is assigned an initial terrain value based on its altitude - mountain, hill, plains, or ocean.

### Zones
1. The map is carved into roughly equal-sized zones as a voronoi diagram. 
1. Each zone is assigned a type (Civilized, Wild, Frontier, Nautical, etc.). The assignment is based on a variety of factors, including terrain in the zone, an effort to balance the variety and number of different zone types, and the need to create an easy starting area. Some zone types will also change the local terrain (e.g. a Desolation replaces plains and forests with desert).
1. Zones are then populated randomly with sites determined by their on type - settlements, tombs, dungeons, etc. Settlements cause forest and plains nearby to be replaced with settled plains, to a radius determined by site size. 

### Road Network

The road network is created by generating a minimum spanning-tree among populated sites within each settled region. 

### Names

Zones, sites, and heroes are randomly assigned names based on JSON lists of lists. 

## Screenshots
Recruiting units:
![Recruiting units](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/recruiting.png)

Fighting enemies:
![Fighting enemies](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/combat.png)

Minimap up with the full map revealed (the current viewport is shown as a white rectangle):
![Minimap](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/minimap.png)
