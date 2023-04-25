




# db_cursor.execute("""
#         INSERT INTO game_info (
#             matchup_id, game_role, player_name, champion_name, role, kills, deaths, assists,
#             item_1, item_2, item_3, item_4, item_5, item_6, trinket
#         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """, (matchup_id, game_role, *player1))

#     db_cursor.execute("""
#         INSERT INTO game_info (
#             matchup_id, game_role, player_name, champion_name, role, kills, deaths, assists,
#             item_1, item_2, item_3, item_4, item_5, item_6, trinket
#         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """, (matchup_id, game_role, *player2))