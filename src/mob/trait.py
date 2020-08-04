'''
Created on Nov 1, 2012

@author: Chris
'''

#traits:
AQUATIC = "Aquatic"             # boolean : can only move in oceans
ARMY_ATTACK = "Army attack"     # boolean  : attacks (ranged and normal) can affect army units
ARMY_FLIGHT = "Army flight"     # boolean : as flight, but can carry rest of group 
ASSASSIN = "Assassin"           # boolean : ranged attacks target leaders,\nif present.
AVARICE = "Avarice"             # numerical: will only join a player with X or > gold
BLACK_MANA = "Black mana"
BLEND = "Blend"             
BLOODTHIRST = "Bloodthirst"
BLOOD_POWER = "Blood power"
BUILD= "Build"                  # string : can build site of given type.  Level of site will = unit level
BURN= "Burn"                    # numerical : 10X% chance to inflict BURNING after hitting a target
BURNING = "Burning"             # boolean : 50/50 chance of being wounded at start of turn, then lose BURNING
CRUSHING_BLOW = "Crushing blow" # numerical: successful melee strikes also hit X units behind target 
ROTTING = "Dead"                   # numerical: counts down days until unit vanishes, like SUMMONED
DEADLY_BLOW = "Deadly blow"     
DEATH_AURA = "Death aura"       # numerical: highest present applied as penalty to Heal/Revive of every unit present
DIPLOMAT = "Diplomat"           # numerical: lets you gain income from a friendly site
ELUSIVE = "Elusive"    
EVADE = "Evade"                 # numerical: penalty to ranged attack strength against this unit
EXHAUSTED = "Exhausted"         # numerical: penalty to strength from fighting
EXTRA_SPELL = "Extra spell"
EXTRA_WOUND = "Extra wound"
FLAMEPROOF = "Flameproof"       # boolean: if true, immune to BURNING effect
FLIGHT = "Flight"               # boolean : can move over any terrain at move cost 1
GRANT_STRENGTH = "Grant strength"     # numerical
GREEN_MANA = "Green mana"
GUARDIAN = "Guardian"     
HAGGLER = "Haggler"             # numerical: x5 = % cost reduction for hiring units
HEAL = "Heal"                    # numerical: x10 = chance to heal nearest wounded unit at end of combat
HEAVY_ARMOR = "Heavy armor"
HERO = "Hero"                   # boolean: indicates if units hero or not
HIDDEN = "Hidden"
HONOR = "Honor"                 # numerical: will only join players with reputation >= to their honor
INFECT = "Infect"               # boolean: when this unit kills an enemy, that enemy is destroyed, and the killer reproduces, if there's room in the stack
INSPIRE = "Inspire"             # numerical: bonus to army unit attack
INSPIRED = "Inspired"           # numerical: temporary indication of bonus received from Inspired
#SUPPORT = "Support"              # boolean :  is target for assassins
LIFE_AURA = "Life aura"         # numerical: highest present applied as bonus to Heal/Revive of every unit present
LIGHT = "Light army"            # boolean  :army unit with this doesn't take damage in unsettled areas
LONG_RANGE = "Long range"
NAVAL = "Naval"                 # numerical: move cost multiplier on water
MOUNTAINEER = "Mountaineer"     # boolean  : group can enter mountains
PATHFINDER = "Pathfinder"       # numerical: bonus to group move
PIERCE = "Pierce"               # numerical: penalty to target armor (more swingy alternative: x10 = chance to insta-kill rather than wound units of same level or less)
PILLAGER = "Pillager"           # boolean: unit pillages settled territory.  doesn't need supply
QUEST = "Quest"                 # boolean: unit grants a treasure if slain by a lone hero
RANGED = "Ranged"               # numerical: ranged attack strength - single roll targeted at unit 1 closer to front in opposing group
                                #            or first opposing unit, if ranged attacker at front.  If no target, not shot.
RED_MANA = "Red mana"
REGENERATE = "Regenerate"       # boolean  : returns from dead to wounded at start of turn
REPUTATION = "Reputation"         # numerical: modifier to reputation when hired
RESTORE = "Restore"
RESTRAIN = "Restrain"           # numerical: if unit hits, inflicts this penalty to str  of target
REVIVE = "Revive"                # numerical: as healer, but dead -> wounded
RAGE = "Rage"                   # numerical: attack bonus / defense penalty when wounded     
RELENTLESS = "Relentless"
RESTRAINED = "Restrained"       # numerical: temporary trait indicating effect of Restrain.  Goes away at start of turn.
SCOUT = "Scout"                 # numerical: bonus to visibility range of group
SLOWED = "Slowed"               # numerical: penalty to movement.  Goes away at start of turn.
SPLASH = "Splash"               # boolean :  if true, successful ranged attacks also target neighbors of normal target      
STEALTH = "Stealth"
STUBBORN = "Stubborn"
SUMMON = "Summon"               # string: at start of turn, if unit of given type not present in stack (and there's room) add one (summoning wounds summoner??)
SUMMONED = "Summoned"           # numerical: indicates how many days a summoned unit has left before disbanding
SUPPLY = "Supply"               # boolean: indicates that this unit can take a wound to keep other armies from taking a wound when out of settled areas
SYLVAN = "Sylvan"               # boolean: if true can't enter civilized areas
SWARM = "Swarm"
SPOT = "Spot"
UNCHAINABLE = "Unchainable"     # boolean: if true, immune to RESTRAINED effect
VAMPIRIC = "Vampiric"           # boolean: heals if it inflicts damage during combat
WHITE_MANA = "White mana"
WILD = "Wild"                   # numerical: will only join player if sites owned <= #

#unimplemented traits
         # boolean: whether or not trial of strength successful in melee, index advances
MASS_HEAL = "Mass Heal"
MASS_REVIVE = "Mass Revive"
SLOW = "Slow" 

# stat mod traits
STRENGTH_MOD = "Strength"
ARMOR_MOD = "Armor"
LOOT_MOD = "Looting"
SPEED_MOD = "Speed"
REPUTATION_MOD = "Reputation"
INCOME_MOD = "Income"
stat_mods = [STRENGTH_MOD, ARMOR_MOD, LOOT_MOD, SPEED_MOD, REPUTATION_MOD, INCOME_MOD]

MAX_RANGE = 3      

tool_tip_table = {
    STRENGTH_MOD: "modifier to unit's strength",
    ARMOR_MOD: "modifier to unit's armor",
    LOOT_MOD: "modifier to unit's looting",
    SPEED_MOD: "modifier to unit's speed",
    #REPUTATION_MOD: "modifier to player's reputation",
    INCOME_MOD: "modifier to player's income",
    AQUATIC : "can only move in oceans",
    ARMY_ATTACK : "attacks (ranged and normal)\ncan affect army units",
    ARMY_FLIGHT : "group ignores terrain",
    ASSASSIN : "ranged attacks target support units,\nif present",
    AVARICE :" will only join a player\n with  or more gold",
    BLACK_MANA: "generates black mana in this hex",
    BLEND: "can become hidden in settled areas",
    BLOODTHIRST: "+X strength and ranged for\neach adjacent wounded unit",
    BLOOD_POWER: "Bonus to strength and ranged from Bloodthirst",
    BUILD   : " can build site of given\ntype for gold",
    BURN :  " 10 X% chance with each hit\nto inflict Burning condition",
    BURNING : "At start of turn,\n 50% chance\n of taking wound",
    CRUSHING_BLOW : "successful melee strikes\nalso hit X units behind target",
    ROTTING :  "counts down days until\ndead unit vanishes",
    DEADLY_BLOW : "successful melee strikes inflict X wounds",
    DEATH_AURA : "penalty to Heal/Revive\nof every unit present",
    DIPLOMAT : "can build embassy at friendly site of level <= X,\ngenerates 1/2 of the site's income",
    ELUSIVE : "always blocks attacks by army units\n (negates army attack)",
    EVADE: "penalty to ranged attacks\nagainst this unit",
    EXHAUSTED: "penalty to strength from previous fights",
    EXTRA_SPELL: "X additional spell slots",
    EXTRA_WOUND: "X additional wounds",
    FLAMEPROOF: "immune to Burning",
    FLIGHT : "ignores terrain",
    GRANT_STRENGTH: "bonus to strength of\nunit in front of this one",
    GREEN_MANA: "generates green mana in this hex",
    GUARDIAN : "unit behind this one can\n borrow its armor value.",
    HEAL : "10 X% chance to heal\nnearest wounded unit",
    HERO : "can carry items",
    HAGGLER: "gives a 5 X% hiring discount",
    HEAVY_ARMOR: "armor doubled vs.\nnon-splash ranged attacks",
    HIDDEN: "can't be seen or attacked by other players",
    HONOR : "requires reputation >= X",
    INFECT: "if this unit kills a unit,\nit summons a unit of type X",
    INSPIRE : "bonus to strength of army units",
    INSPIRED: "bonus to strength from Inspire",
#    SUPPORT : "is target for assassins",
    LIFE_AURA : " bonus to Heal/Revive\nof every unit present",
    LIGHT : "does not require supply",
    LONG_RANGE: "ranged attacks will strike\nup to " + str(MAX_RANGE) + " slots ahead",
    NAVAL : "group can enter water,\nmove cost mult. by X",
    MOUNTAINEER : "group can enter mountains",
    PATHFINDER : "bonus to group move",
    PIERCE : "penalty to target's armor",
    PILLAGER: "pillages settlement,\ndoes not require supply",
    QUEST: "Heroes only need apply",
    RANGED : "X : strength of ranged attack",
    RED_MANA: "generates red mana in this hex",
    REGENERATE : "returns from dead\nto wounded at start of turn",
    RELENTLESS: "suffers no exhaustion penalties\nfrom fighting multiple foes",
    REPUTATION_MOD: "modifier to player's reputation",
    RESTORE: "use to heal frontmost wounded\nunit, refreshed weekly",
    RESTRAIN : "inflicts penalty to\nstrength of target on hit",
    REVIVE : "10 X% to revive\n nearest dead unit",
    RAGE : "strength bonus/armor penalty\n when wounded",     
    RESTRAINED : "Strength penalty.\nGoes away at start of turn",
    SCOUT : "bonus to visible range\nof group",
    SLOWED : " penalty to movement.\nGoes away at start of turn",
    SPLASH : "successful ranged attacks\ntarget neighbors of normal target",
    STEALTH : "can become hidden in forests",
    STUBBORN: "group with this unit will never retreat",
    SUMMON : "adds unit of type X\nat start of turn",
    SUMMONED : "counts down days until\nsummoned unit vanishes",    
    SUPPLY : "X = days worth of supply\nfor armies in this group",
    SWARM : "if an attack would kill this unit,\nit instead wounds another healthy Swarm unit, if possible" , 
    SYLVAN: "cannot enter settled areas",     
    SPOT: "can see hidden units",
    UNCHAINABLE: "immune to Restrained",
    VAMPIRIC: "if this unit wounds a unit,\nit heals itself",
    WHITE_MANA: "generates white mana in this hex",
    WILD: "will only join a player that\n owns X or fewer sites"
}


def trait_str(trait_name, trait_value):
    trait_text = trait_name
    if not isinstance(trait_value, bool):
        if trait_name in stat_mods:
            trait_text = str(trait_value) + " " + trait_text
            if trait_value > 0:
                trait_text = "+" + trait_text
        else:
            trait_text += " " + str(trait_value)
    return trait_text
   

support_traits = [SUMMON, INSPIRE, HEAL, REVIVE, PATHFINDER, SUPPLY, HERO, DIPLOMAT]
leader_traits = [INSPIRE, HEAL, REVIVE]
consumable_traits = [SUPPLY, RESTORE]
useable_traits = [RESTORE]
negating_traits = {ARMY_ATTACK : ELUSIVE} # key negated by value trait

