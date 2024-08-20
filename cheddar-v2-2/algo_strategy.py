import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.to_upgrade = []
        self.damaged_regions = [0,0,0,0] # left, left-middle, right-middle, right

        self.back_support_locations = []
        self.is_edge_spam_threshold = 0
        self.is_left_edge_spam = 0
        self.is_right_edge_spam = 0
        limit = [13,14]
        for i in range(0,5):
            for j in range(limit[0],limit[1]+1):
                self.back_support_locations.append([j,i])
                limit[0] -= 1
                limit[1] += 1
        self.prev_turn_info = 0

        self.attack_location = None
        self.start_attack_turn = 3
        self.attacks_left = 3

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        self.attack(game_state) # support at round 1
        self.build_defences(game_state)
        self.build_defences_stage_2(game_state)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """

        # initial defense
        turrets = [[10,12],[17,12],[4,12],[23,12]]
        walls = [[10,13],[17,13],[4,13],[23,13]]

        game_state.attempt_spawn(TURRET, turrets) 
        game_state.attempt_upgrade(turrets)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_upgrade(walls)

        # determine if enemy is edge spammer or they spawn randomly
        if self.is_edge_spam(game_state):
            # spawn turrets on the edges
            if self.is_left_edge_spam < self.is_right_edge_spam: 
                # coordinates are reversed for some reason
                left_turrets = [[4,12],[3,12],[2,12],[1,12]]
                self.attempt_spawn_and_upgrade(game_state, left_turrets)
            else:
                right_turrets = [[23,12],[24,12],[25,12],[26,12]]
                self.attempt_spawn_and_upgrade(game_state, right_turrets)
            
        new_turrets = [[3,12],[24,12],[9,12],[18,12]]
        self.attempt_spawn_and_upgrade(game_state, new_turrets)

        # third turrets
        third_turrets = [[5,12],[22,12]]
        game_state.attempt_upgrade(third_turrets)

        # final_turrets, edge_walls
        edge_walls = [[0,13],[27,13],[1,13],[26,13],[2,13],[25,13]] 
        for location in edge_walls:
            game_state.attempt_spawn(WALL,location)
            game_state.attempt_upgrade(location)

        game_state.attempt_upgrade(third_turrets)

    def build_defences_stage_2(self, game_state):
        pass
                
    def attack(self, game_state):
        attack_options = [[1,12],[2,11],[3,10],[4,9],[5,8],[6,7],[7,6],[8,5],[9,4],[10,3],[11,2],[12,1],[13,0],
                          [14,0],[15,1],[16,2],[17,3],[18,4],[19,5],[20,6],[21,7],[22,8],[23,9],[24,10],[25,11],[26,12]]

        # def pick_support_location():
        #     location = [self.attack_location[0], self.attack_location[1] + 1]
        #     if not game_state.contains_stationary_unit(location) and game_state.in_arena_bounds(location):
        #         return location
            
        #     if game_state.in_arena_bounds(location):
        #         if self.attack_location[0] <= 13:
        #             return [self.attack_location[0] + 1, self.attack_location[1]]

        if game_state.turn_number == self.start_attack_turn:
            self.attacks_left -= 1

            self.attack_location = self.least_damage_spawn_location(game_state, attack_options)
            game_state.attempt_spawn(SCOUT, self.attack_location, 10000)

            support_location = [self.attack_location[0], self.attack_location[1] + 1]
            game_state.attempt_spawn(SUPPORT, support_location, 1)
            # game_state.attempt_remove(support_location)
        elif game_state.turn_number > self.start_attack_turn and game_state.turn_number % 2 == self.start_attack_turn % 2:
            self.attacks_left -= 1

            game_state.attempt_spawn(SCOUT, self.attack_location, 10000)
 
            support_location = [self.attack_location[0], self.attack_location[1] + 1]
            game_state.attempt_spawn(SUPPORT, support_location, 1)
            game_state.attempt_remove(support_location)

        if self.attacks_left == 0:
            support_location = [self.attack_location[0], self.attack_location[1] + 1]
            game_state.attempt_remove(support_location)
            
            self.attack_location = None
            self.start_attack_turn = game_state.turn_number + 4
            self.attacks_left = 3

    def is_edge_spam(self, game_state):
        # check for support at the back 
        for location in self.back_support_locations:
            if game_state.contains_stationary_unit(location):
                self.is_edge_spam_threshold += 1

        # variable is updated if they spam scouts in the back
        
        if self.is_edge_spam_threshold + self.is_left_edge_spam + self.is_right_edge_spam >= 3: 
            return True
        else:
            return False



    def least_damage_spawn_location(self, game_state, location_options): 
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            try:
                damage = 0
                for path_location in path:
                    attackers = game_state.get_attackers(path_location, 0)
                    # Get number of enemy turrets that can attack each location and multiply by turret damage
                    damage += len(attackers) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                damages.append(damage)
            except:
                damages.append(10000)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))
        damages = events["damage"]
        for damage in damages:
            location = damage[0]
            unit_owner_self = True if damage[4] == 1 else False
            if unit_owner_self:
                region = location[0] // 8
                self.damaged_regions[region] += damage[1]

        turn_info = state["turnInfo"]
        if self.prev_turn_info==0 and turn_info==1:
            spawns = events['spawn']
            num_left_scouts_spawned = 0
            num_right_scouts_spawned = 0
            for spawn in spawns:
                # scout spawned in their back
                if spawn[1]==3 and spawn[0][1] >= 23:
                    if spawn[0][0] <= 13 :
                        num_left_scouts_spawned +=1
                    else:
                        num_right_scouts_spawned +=1                        
            
            if num_left_scouts_spawned >= 5:
                self.is_left_edge_spam += 1
            elif num_right_scouts_spawned >= 5:
                self.is_right_edge_spam += 1


        
        # gamelib.debug_write("Damages: {}".format(self.damaged_regions))

    
    def attempt_spawn_and_upgrade(self, game_state, locations):
        for location in locations:
            choice = random.randint(0,1)
            if choice == 0:
                game_state.attempt_spawn(TURRET,location)
                game_state.attempt_upgrade(location)
                game_state.attempt_spawn(WALL,[location[0], location[1] + 1])
                game_state.attempt_upgrade([location[0], location[1] + 1])
            else:
                game_state.attempt_spawn(WALL,[location[0], location[1] + 1])
                game_state.attempt_upgrade([location[0], location[1] + 1])
                game_state.attempt_spawn(TURRET,location)
                game_state.attempt_upgrade(location)

if __name__ == "__main__":
    algo = AlgoStrategy() 
    algo.start()
