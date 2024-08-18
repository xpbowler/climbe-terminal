import gamelib
import random
import math
import warnings
from sys import maxsize
from collections import namedtuple
import json
import random
from operator import itemgetter

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

        self.central_wall_locations = [[11,8][12,8],[13,8],[14,8],[15,8],[16,8]]
        
        self.left_peripheral_wall_locations = [[0,13],[1,13],[2,13],[3,12],[5,11],[6,11]]

        self.right_peripheral_wall_locations = [[27,13],[226,13],[25,13],[24,12],[22,11],[21,11]]

        self.all_attack_options = []
        for i in range(0,14):
            self.all_attack_options.append([i,13-i])
            self.all_attack_options.a
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.strategy(game_state)

        game_state.submit_turn()

    def strategy(self, game_state):
        self.early_game(game_state)  

    def early_game(self, game_state):

        # opening
        turret_locations = [[17,9],[10,9],[4,11],[23,11]]
        game_state.attempt_spawn(TURRET, turret_locations)
        wall_locations = [[4,12],[23,12]]
        game_state.attempt_spawn(WALL, wall_locations)
        game_state.attempt_upgrade(wall_locations)
        
        # build out walls equally on both ssides
        if self.left_wall_peripheral_locations.len
    
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
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
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

    def should_right_be_open(game_state, weights=None):
        if not weights:
            weights = [1, 6]

        weights_by_def_unit = dict(zip([WALL, TURRET], weights))

        left_strength, right_strength = (0, 0)

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (
                        unit.unit_type == TURRET or unit.unit_type == WALL
                    ):
                        if location[0] < 10:
                            left_strength += weights_by_def_unit[unit.unit_type]
                        elif location[0] > 17:
                            right_strength += weights_by_def_unit[unit.unit_type]

        if left_strength > right_strength:
            right = True
        elif left_strength < right_strength:
            right = False
        else:
            right = bool(random.randint(0, 1))
        return right

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
