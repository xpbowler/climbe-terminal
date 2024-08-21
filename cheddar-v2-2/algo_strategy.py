import gamelib
import random
from sys import maxsize
from gamelib.unit import GameUnit
import json

"""
# TODO:
1. +random(2,3) for attack
2. predict & intercept
3. consider putting support on top first
5. side strat to destroy support along side
6. spam middle
"""

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
        self.attack(game_state) # support at round 1
        self.build_defences(game_state)
        self.build_defences_stage_2(game_state)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """

        # basic initial defense
        # change from 4,12 and 23, 12 to 3,12 and 24,12
        # this is meant to counter the meta
        turrets = [[10,11],[17,11],[3,12],[24,12]]
        turrets_2 = [[9,11],[18,11]]
        walls = [[10,12],[17,12]]
        walls_2 = [[3,13],[24,13]]
        
        game_state.attempt_spawn(TURRET, turrets)
        game_state.attempt_upgrade(turrets)
        game_state.attempt_spawn(TURRET, turrets_2)
        game_state.attempt_spawn(WALL, walls_2)
        game_state.attempt_upgrade(walls_2)
        game_state.attempt_spawn(WALL, walls)
        game_state.attempt_upgrade(walls)

        if self.is_middle_spam >= 2:
            # beef up the middle
            middle_turrets = [[12,12],[15,12]]
            self.attempt_spawn_and_upgrade(game_state, middle_turrets)
            self.is_middle_spam -= 1

        # beef up edges if enemy is edge spammer
        if self.is_edge_spam(game_state):
            # spawn turrets on the edges depending on which side is weaker
            gamelib.debug_write(f"Left health: {self.left_health}\nRight health: {self.right_health}")
            if self.right_health > self.left_health:
                # coordinates are reversed for some reason
                left_turrets = [[4,12],[3,12]]
                self.attempt_spawn_and_upgrade(game_state, left_turrets)
            else:
                right_turrets = [[23,12],[24,12]]
                self.attempt_spawn_and_upgrade(game_state, right_turrets)
            
            self.is_edge_spam_threshold -= 0.75

        if self.alot_edge_spam(game_state):
            if self.right_health > self.left_health:
                # coordinates are reversed for some reason
                left_turrets = [[5,12]]
                self.attempt_spawn_and_upgrade(game_state, left_turrets)
            else:
                right_turrets = [[22,12]]
                self.attempt_spawn_and_upgrade(game_state, right_turrets)

    def build_defences_stage_2(self, game_state):
        turrets = [
            [[3,12],[4,12],[5,12]],
            [[24,12],[23,12],[22,12]],
            [[13,12],[11,12],[16,12],[9,12],[18,12]]
        ]

        self.evenly_strengthen(turrets, [1.4,1.4,1],game_state)

        new_turrets = [[9,12],[16,12],[3,12],[24,12],[18,12],[5,12]]
        self.attempt_spawn_and_upgrade(game_state, new_turrets)
        edge_walls = [[0,13],[27,13],[1,13],[26,13],[2,13],[25,13]]
        for location in edge_walls:
            game_state.attempt_spawn(WALL,location)
            game_state.attempt_upgrade(location)
        new_turrets_2 = [22,12],[2,12],[25,12]
        self.attempt_spawn_and_upgrade(game_state, new_turrets_2)
        
        self.evenly_strengthen([self.left_final_turrets, self.right_final_turrets, self.middle_final_turrets],[1,1,1],game_state)
        # now we can start opening holes

        
    def evenly_strengthen(self, turrets, multipliers, game_state):
        # division for three sections is 8 and 18. 
        # left: 0-8
        # middle: 8-18
        # right: 18-27
        # strengthen the weakest part

        strengths = [self.left_health*multipliers[0], self.right_health*multipliers[1], self.middle_health*multipliers[2]]
        weakest_index = strengths.index(min(strengths))
        self.attempt_spawn_and_upgrade(game_state,turrets[weakest_index])

                
    def attack(self, game_state):
        # attack_options = [[0,13],[1,12],[2,11],[3,10],[4,9],[5,8],[6,7],[7,6],[8,5],[9,4],[10,3],[11,2],[12,1],[13,0],
        #                   [14,0],[15,1],[16,2],[17,3],[18,4],[19,5],[20,6],[21,7],[22,8],[23,9],[24,10],[25,11],[26,12],[27,13]]

        # attack_options = [[0,13],[5,8],[8,5],[19,5],[22,8],[27,13]]
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

            self.start_attack_turn = int(game_state.turn_number + random.randint(2, 3))

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

    def weakest_quadrant(self, game_state):
        quadrants = [0,0,0,0]

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and unit.unit_type == TURRET:
                        quadrants[unit.x//7] += 1.0*(unit.health/75) if unit.upgraded else 0.5*(unit.health/75)

        return quadrants.index(min(quadrants))

    def destroy_turrets_location(self, game_state, location_options):
        importance = []
        start_units = game_state.MP - 2 # leeway for 2+ survivers
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path is None or path[-1] in game_state.game_map.get_edge_locations(game_state.get_target_edge(location)):
                importance.append(-1)
                continue
            clone_state = game_state.deepclone()
            units_health = start_units * 12

            destroyed = False
            for path_location in path:
                attackers = clone_state.get_attackers(path_location,0)
                units_health -= len(attackers) * gamelib.GameUnit(TURRET, clone_state.config).damage_i

                target = clone_state.get_target(GameUnit(SCOUT, clone_state.config))
                num_units = (units_health + 11) // 12

                if units_health <= 0:
                    break

                if target is not None:
                    # decrease target health
                    clone_state.game_map[target.x][target.y] -= num_units * 2 
                    if clone_state.game_map[target.x][target.y] <= 0:
                        # remove from map
                        clone_state.game_map.remove_unit([target.x, target.y])
                        if target.unit_type == TURRET:
                            destroyed = True

            importance.append(1 if destroyed else 0)
        if max(importance) <= 0:
            return None
        return location_options[importance.index(max(importance))]

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

            # gamelib.debug_write(f'{location} : {path}')
            if path is not None and path[-1] in game_state.game_map.get_edge_locations(game_state.get_target_edge(location)):
                damage = 0
                for path_location in path:
                    attackers = game_state.get_attackers(path_location, 0)
                    # Get number of enemy turrets that can attack each location and multiply by turret damage
                    damage += len(attackers) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                damages.append([damage, location[1]]) # compare by damage then location
            else:
                damages.append([10000, location[1]])

        # gamelib.debug_write(f'========= Least damage spawn location : {location_options[damages.index(min(damages))]} ==========')
        # for i in range(len(damages)):
        #     gamelib.debug_write(f'{location_options[i]} : {damages[i]}')

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


    def attempt_spawn_and_upgrade(self, game_state, locations):
        for location in locations:
            # choice = random.randint(0,1)
            # if choice == 0:
            game_state.attempt_spawn(TURRET,location)
            game_state.attempt_upgrade(location)
            game_state.attempt_spawn(WALL,[location[0], location[1] + 1])
            game_state.attempt_upgrade([location[0], location[1] + 1])
            # else:
            #     game_state.attempt_spawn(WALL,[location[0], location[1] + 1])
            #     game_state.attempt_upgrade([location[0], location[1] + 1])
            #     game_state.attempt_spawn(TURRET,location)
            #     game_state.attempt_upgrade(location)

if __name__ == "__main__":
    algo = AlgoStrategy() 
    algo.start()
