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

        self.is_right_opening = True
        self.wall_locations = [
            [0, 13],
            [1, 13],
            [5, 13],
            [6, 13],
            [7, 13],
            [8, 13],
            [9, 13],
            [11, 13],
            [12, 13],
            [13, 13],
            [14, 13],
            [15, 13],
            [16, 13],
            [18, 13],
            [19, 13],
            [20, 13],
            [21, 13],
            [22, 13],
            [26, 13],
            [27, 13],
        ]

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

        filter_locs, self.is_right_opening, save_sp = early_game(game_state, self.is_right_opening, self.wall_locations)

        if game_state.turn_number > 4:
            
            if not save_sp:
                build_defences(game_state, self.is_right_opening, filter_locs)
            
            if self.is_right_opening:
                demolisher = [[4,9]]
            else:
                demolisher = [[23,9]]
            game_state.attempt_spawn(SCOUT, demolisher, 1000)

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

def early_game(
    game_state, is_right_opening, filter_locs
):

    turret_locations = [[2, 13], [3, 13], [10, 13], [17, 13], [24, 13], [25, 13]]
    game_state.attempt_spawn(TURRET, turret_locations)
    save_sp = False

    if not all(map(game_state.contains_stationary_unit, turret_locations)):
        save_sp = True

    if game_state.turn_number < 4:
        return [], True, save_sp

    final_filter_locs = list(filter_locs)

    if game_state.turn_number % 4 == 0:
        is_right_opening = should_right_be_open(game_state)

    if is_right_opening:
        remove_filter_at = [[23, 13]]
        final_filter_locs.append([4, 13])

    else:
        remove_filter_at = [[4, 13]]
        final_filter_locs.append([23, 13])

    game_state.attempt_remove(remove_filter_at)

    final_filter_locs.sort(key=itemgetter(0), reverse=(not is_right_opening))

    game_state.attempt_spawn(WALL, final_filter_locs)
    return final_filter_locs, is_right_opening, save_sp


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

def build_defences(game_state, is_right_opening, filter_locs):

    encryptor_locations = [[10, 10], [17, 10]]
    game_state.attempt_spawn(SUPPORT, encryptor_locations)
    game_state.attempt_upgrade(encryptor_locations)

    destructor_locations = (
        [[25, 12], [24, 11], [24, 10]]
        if is_right_opening
        else [[2, 12], [3, 11], [3, 10]]
    )
    game_state.attempt_spawn(TURRET, destructor_locations)

    encryptor_locations = [[10, 8], [17, 8]]
    game_state.attempt_spawn(SUPPORT, encryptor_locations)
    game_state.attempt_upgrade(encryptor_locations)

    if all(map(game_state.contains_stationary_unit, destructor_locations)):
        game_state.attempt_upgrade(filter_locs)

    destructor_locations = [
        [17, 11],
        [6, 8],
        [10, 11],
        [15, 9],
        [12, 9],
        [15, 6],
        [12, 6],
    ]
    game_state.attempt_spawn(TURRET, destructor_locations)

    # Upgrade destructors in the back
    game_state.attempt_upgrade([[3, 10], [24, 10]])


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
