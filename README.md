I created this game in 2012-2013 using Python 2.7 and Pygame to try out procedural generation of terrain, rivers, road nets, monster lairs, etc. The (very bad) art and sound effects are my own.

Unfortunately it was more fun to build than it is to play :-) 

The most interesting files are:
* [src/gamemap/hexmap.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/hexmap.py) (Code for handling all the different states of a map location)
* [src/gamemap/map_maker.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/map_maker.py) (Code for generating the map before the start of the game).
* [src/gamemap/road.py](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/gamemap/road.py) (Code for generating a road net between settlements)

Among other things you can:
* Recruit new units and heroes at settlements
* Conquer settlements
* Defeat lairs full of monsters
* Find treasures and equip them onto your heroes
* Enter ever more dangerous territories in search of more dangerous monsters and more powerful units and treasures

## Screenshots
Main menu:
![Main menu](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/mainmenu.png)

Recruiting units:
![Recruiting units](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/recruiting.png)

Fighting enemies:
![Fighting enemies](https://github.com/cfmcdonald-78/Hexcrawler/blob/master/src/images/combat.png)
