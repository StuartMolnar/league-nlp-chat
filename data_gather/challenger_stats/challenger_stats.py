import requests
import time
import os
import datetime
from dotenv import load_dotenv
from challenger_games import ChallengerGames

# Load environment variables from the .env file
load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'




def main():
    cg = ChallengerGames()

    # Get challenger games from the past day
    games_past_day = cg.get_challenger_games_past_day()
    print("Challenger games in the past day:")
    print(games_past_day)

    # Get the playerNameMap dictionary
    player_name_map = cg.playerNameMap
    print("Player Name Map:")
    print(player_name_map)
    
if __name__ == '__main__':
    main()

#layout of json:
# (for all ids use ddragon api to get the names)
# {participants: [0 - 10]
# 	champion name: 
# 	item0: (ignore if id is 0)
# 	item1:
# 	item2:
# 	item3:
# 	item4:
# 	item5:
# 	item6:
#   position:
# 	matchup: (find enemy player with same role)
#   individualPosition: (replace UTILITY entries with SUPPORT)
#   for runes look through "styles" and do more research



#info to grab:
# champion
# position
# summoner name
# champion matchup
# build
# runes
# ban

# create database to store info

# if player name not in map, get name from puuid api and add to map

# table by champion

# 	vi
# 		summoner name
# 		position
# 		versus karthus
# 		build [item 1, item 2, item 3, ...]
# 		runes [rune 1, rune 2, rune 3, ...]
# 		ban morgana
		
# 	kat
# 		...
	
# 	...

