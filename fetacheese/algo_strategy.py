import gamelib
import random
import math
import warnings
from sys import maxsize
import json

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

        self.turrets = [[]]

        self.scouts = [[12,1],[15,1]]

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
        # Setup main defense stucture
        self.build_defences(game_state)
        # Now let's analyze the enemy base to see where their defenses are concentrated.
        # If they have many units in the front we can build a line for our demolishers to attack them at long range.
        # if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
        # if 1==1: #not using this rn
        #     self.demolisher_line_strategy(game_state)
        # else:
        #     # send scouts to weaker side
        #     if self.should_right_be_open: 
        #         # we want to send a lot of scouts at once (16+)
        #         if game_state.MP > 18:
        #             game_state.attempt_spawn(SCOUT, self.scouts[1],1000)
        #     else:
        #         if game_state.MP > 18:
        #             game_state.attempt_spawn(SCOUT, self.scouts[0],1000)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        if game_state.turn_number != 0 and game_state.turn_number%4 == 0:
            # spawn supports
            support_locations = [[12,6],[15,6],[12,5],[15,5],[12,4],[15,4],[12,3],[15,3]]
            game_state.attempt_spawn(SUPPORT, support_locations)
        # initial setup
        turret_locations = [[4,12],[25,12],[11,8],[20,10],[3,13],[26,13],[6,10],[15,8],[2,13],[27,13],[6,11],[22,12],[12,8],[21,12],[19,10],[8,8],[17,8],[1,13],[6,12],[24,12],[13,8],[18,9]]
        for loc in turret_locations:
            game_state.attempt_spawn(TURRET, [loc])
            game_state.attempt_upgrade([loc])

        # right_wall_holes = [[]]
        # left_wall_holes = [[]]
        if self.should_right_be_open:
            # open hole on left --> scouts will go to right side
            pass
        else:
            # open hole on right --> scouts will go to left side
            pass

        # wall_holes = [[0,13],[5,12],[7,9],[9,8],[10,8],[14,8],[16,8],[21,11],[23,12]]
        # game_state.attempt_spawn(WALL, wall_holes)
        # game_state.attempt_remove([random.choice(wall_holes)])

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """

        game_state.attempt_spawn(TURRET, self.left_hook)
        game_state.attempt_spawn(TURRET, self.right_hook)

        game_state.attempt_spawn(TURRET, self.front_tunnel)

        game_state.attempt_spawn(TURRET, self.front_tunnel_turrets)
        game_state.attempt_upgrade(self.front_tunnel_turrets)

        # fill out tunnel
        game_state.attempt_spawn(TURRET, self.back_tunnel)
        game_state.attempt_spawn(TURRET, self.back_tunnel_turrets)
        game_state.attempt_upgrade(self.back_tunnel_turrets)

        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

        # spawn one support so that scouts can survive 2 hits
        game_state.attempt_spawn(SUPPORT, self.supports[0])

    def stall_with_interceptors(self, game_state):
        game_state.attempt_spawn(INTERCEPTOR, [18,4],1)
        game_state.attempt_spawn(INTERCEPTOR, [7,6],1)

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

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
                # gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                # gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

    def should_right_be_open(self, game_state, weights=None):
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


    def spawn_units(self, game_state, locations):
        for location in locations:
            game_state.attempt_spawn(location[0], [location[1:]])
            if location[0] == TURRET:
                game_state.attempt_upgrade([location[1:]])

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
