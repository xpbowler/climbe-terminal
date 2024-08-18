
def opening_defense(game_state):
    """
    we use a pure ironclad opening for the first turn.
    
    - good defense, easy to expand into great wall of china
    - use interceptors as defense
    """
    
    # positions
    interceptors = [[11,2],[12,23]]
    upgraded_turrets = [[3,12], [24,12]]
    upgraded_walls = [[3,13], [24,13]]
    upgraded_support = [[13,0], [14,0]]

    # place units
    game_state.attempt_spawn(game_state.INTERCEPTOR, interceptors)
    game_state.attempt_spawn(game_state.TURRET, upgraded_turrets)
    game_state.attempt_spawn(game_state.WALL, upgraded_walls),
    game_state.attempt_spawn(game_state.SUPPORT, upgraded_support)

    # upgrade units
    game_state.attempt_upgrade(game_state.INTERCEPTOR, interceptors)
    game_state.attempt_upgrade(game_state.TURRET, upgraded_turrets)
    game_state.attempt_upgrade(game_state.WALL, upgraded_walls),
    game_state.attempt_upgrade(game_state.SUPPORT, upgraded_support)

    # 

    