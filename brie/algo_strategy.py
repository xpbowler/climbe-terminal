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
        self.scored_on_locations = []
        self.to_upgrade = []
        self.damaged_regions = [0,0,0,0] # left, left-middle, right-middle, right

        self.back_support_locations = []
        self.is_edge_spam_threshold = 0
        self.is_left_edge_spam = 0
        self.is_right_edge_spam = 0
        self.is_middle_spam = 0
        limit = [13,14]
        for i in range(0,5):
            for j in range(limit[0],limit[1]+1):
                self.back_support_locations.append([j,i])
                limit[0] -= 1
                limit[1] += 1
        self.prev_turn_info = 0

        self.attack_location = None
        self.start_attack_turn = 2
        self.attacks_left = 3

        self.middle_health = 0
        self.left_health = 0
        self.right_health = 0
        self.health_weights = [1,3]

        self.left_final_turrets = []
        for i in range(1,9):
            self.left_final_turrets.append([i,12])
        self.right_final_turrets = []
        for i in range(8,19):
            self.right_final_turrets.append([i,12])
        self.middle_final_turrets = []
        for i in range(18,28):
            self.middle_final_turrets.append([i,12])

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
        self.attack(game_state)
        self.build_defences(game_state)
        self.adaptive_defence(game_state)
        self.build_defences_stage_2(game_state)

    def attack(self, game_state):
        attack_options = [[0,13],[5,8],[22,8],[27,13]]

        def pick_support_location():
            if self.attack_location[1] == 0:
                return [self.attack_location[0], self.attack_location[1] + 1]
            if self.attack_location[1] == 5 or self.attack_location[1] == 8:
                return [self.attack_location[0] + 
                    (2 if self.attack_location[0] <= 13 else self.attack_location[0] - 2),
                    self.attack_location[1]]
            if self.attack_location[1] == 13:
                return [self.attack_location[0] + 
                    (1 if self.attack_location[0] <= 13 else self.attack_location[0] - 1),
                    self.attack_location[1] - 1]
            # path = game_state.find_path_to_edge(self.attack_location)
            # for loc in path:
            #     for dir in [[0,1],[0,-1],[1,0],[-1,0]]:
            #         pos = [loc[0] + dir[0], loc[1] + dir[1]]
            #         if game_state.game_map.in_arena_bounds(pos) \
            #                 and not game_state.contains_stationary_unit([path[0][0] + dir[0], path[0][1] + dir[1]]) \
            #                 and pos not in path:
            #             return pos

            # location = list(self.attack_location)
            # location[0] += 1 if location[0] <= 13 else -1
            # location[1] -= 1 if location[1] >= 1 else 0
            return [10,10]

        # if game_state.turn_number >= self.start_attack_turn:
        #     self.attack_location = self.destroy_turrets_location(game_state, attack_options)
        #     gamelib.debug_write("Attacking at " + str(self.attack_location))
        #     if game_state.turn_number == self.start_attack_turn:
        #         self.attack_location = random.choice(attack_options)
        #         game_state.attempt_spawn(SCOUT, self.attack_location, 10000)
        #     elif self.attack_location is not None:
        #         game_state.attempt_spawn(SCOUT, self.attack_location, 10000)

        #     if game_state.turn_number == self.start_attack_turn or \
        #         self.attack_location is not None:
        #             self.support_location = pick_support_location()
        #             game_state.attempt_spawn(SUPPORT, self.support_location)
        #             game_state.attempt_remove(self.support_location)

        if game_state.turn_number >= self.start_attack_turn:
            # self.attacks_left -= 1

            # self.attack_location = self.destroy_turrets_location(game_state, attack_options)
            self.attack_location = attack_options[self.weakest_quadrant(game_state)]
            game_state.attempt_spawn(SCOUT, self.attack_location, 10000)

            self.support_location = pick_support_location()
            game_state.attempt_spawn(SUPPORT, self.support_location)
            game_state.attempt_remove(self.support_location)
            # gamelib.debug_write("Attacking at " + str(self.attack_location) + " with support at " + str(self.support_location))

            # self.last_attack = game_state.turn_number

            self.start_attack_turn = int(game_state.turn_number + 2)

        # elif game_state.turn_number > self.start_attack_turn and game_state.turn_number == self.last_attack + 3:
        #     self.attacks_left -= 1

        #     game_state.attempt_spawn(SCOUT, self.attack_location, 10000)
 
        #     game_state.attempt_spawn(SUPPORT, self.support_location)

        #     self.last_attack = game_state.turn_number

        #     if self.attacks_left == 0:
        #         game_state.attempt_remove(self.support_location)

        #         self.attack_location = None
        #         self.start_attack_turn = game_state.turn_number + 3
        #         self.attacks_left = 1

    def weakest_quadrant(self, game_state):
        quadrants = [0,0,0,0]

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and unit.unit_type == TURRET:
                        quadrants[unit.x//7] += 1.0*(unit.health/75) if unit.upgraded else 0.5*(unit.health/75)

        return quadrants.index(min(quadrants))

    def evenly_strengthen(self, turrets, multipliers, game_state):
        # division for three sections is 8 and 18. 
        # left: 0-8
        # middle: 8-18
        # right: 18-27
        # strengthen the weakest part

        strengths = [self.left_health*multipliers[0], self.right_health*multipliers[1], self.middle_health*multipliers[2]]
        weakest_index = strengths.index(min(strengths))
        self.attempt_spawn_and_upgrade(game_state,turrets[weakest_index])

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # # Place turrets that attack enemy units
        turret_locations = [[4,13],[5,13],[14,13],[22,13],[23,13]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)

        turret_locations_2 = [[13,13],[3,13]]
        self.attempt_spawn_and_upgrade(turret_locations_2)
        self.attempt_spawn_and_upgrade([[24,13]])
        self.attempt_spawn_and_upgrade([[12,12],[15,12]])
        self.attempt_spawn_and_upgrade([[6,13],[21,13]])

    def adaptive_defence(self, game_state):
        pass

    def build_defences_stage_2(self, game_state):
        turrets = [
            [[2,13]],
            [[25,13]],
            [[11,12],[16,12]]
        ]

        self.evenly_strengthen(turrets, [1,1,1],game_state)
        
        self.evenly_strengthen([self.left_final_turrets, self.right_final_turrets, self.middle_final_turrets],[1,1,1],game_state)
        # now we can start opening holes

    def attempt_spawn_and_upgrade(self, game_state, locations):
        for location in locations:
            game_state.attempt_spawn(TURRET,location)
            game_state.attempt_upgrade(location)

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
        
        self.analyze_enemy_moves_and_our_defense(state, events)

    
    def analyze_enemy_moves_and_our_defense(self, state, events):
        spawns = events['spawn']
        num_left_scouts_spawned = num_right_scouts_spawned = num_middle_scouts_spawned = 0
        self.is_left_edge_spam = self.is_right_edge_spam = 0

        for spawn in spawns:
            if spawn[1] == 3:
                if spawn[0][1] >= 22:
                    if spawn[0][0] <= 13:
                        num_left_scouts_spawned += 1
                    else:
                        num_right_scouts_spawned += 1
                elif 20 <= spawn[0][1] <= 23:
                    num_middle_scouts_spawned += 1

        if num_left_scouts_spawned >= 5:
            self.is_left_edge_spam += 1 
        if num_right_scouts_spawned >= 5:
            self.is_right_edge_spam += 1 
        if num_middle_scouts_spawned >= 5:
            self.is_middle_spam += 1
        # assess at the end of action --> going into deploy phase
        # get the health of middle left and right
        # turret health is 3x more valuable than wall healths

        self.left_health = 0
        self.right_health = 0
        self.middle_health = 0
        units = state["p1Units"]
        walls= units[0]
        turrets = units[2]

        for wall in walls:
            if wall[1]==13:
                if wall[0] < 8:
                    self.left_health += wall[2]
                elif wall[0] >= 8 and wall[0] <= 18:
                    self.middle_health += wall[2]
                else:
                    self.right_health += wall[2]
        for turret in turrets:
            if turret[1]==12:
                if turret[0] < 8:
                    self.left_health += turret[2]*3
                elif turret[0] >= 8 and turret[0] <= 18:
                    self.middle_health += turret[2]*3
                else:
                    self.right_health += turret[2]*3  

    def is_edge_spam(self, game_state):
        # check for support at the back 
        for location in self.back_support_locations:
            if game_state.contains_stationary_unit(location):
                self.is_edge_spam_threshold += 1
                break

        # variable is updated if they spam scouts in the back
        
        if self.is_edge_spam_threshold + self.is_left_edge_spam + self.is_right_edge_spam >= 2: 
            return True
        else:
            return False
    
    def alot_edge_spam(self, game_state):
        # check for support at the back 
        for location in self.back_support_locations:
            if game_state.contains_stationary_unit(location):
                self.is_edge_spam_threshold += 1
                break
            
        if self.is_edge_spam_threshold + self.is_left_edge_spam + self.is_right_edge_spam >= 2.75:
            return True
        else:
            return False 


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
