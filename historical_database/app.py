

# def process_game_data(game_data):
#     matchup_id = 1
#     for game in game_data:
#         for game_role, player_data in game.items():
#             for i in range(0, len(player_data), 2):
#                 player1 = player_data[i]
#                 player2 = player_data[i + 1]
#                 store_matchup(matchup_id, game_role, player1, player2)
#                 matchup_id += 1