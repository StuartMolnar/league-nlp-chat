import requests
import time
import os
import json
import datetime
from dotenv import load_dotenv
from challenger_games import ChallengerGames

# Load environment variables from the .env file
load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'

class MatchData:
    def __init__(self):
        self.ddragonVersion = self.get_latest_ddragon_version()

    def get_latest_ddragon_version(self):
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        if response.status_code == 200:
            versions = response.json()
            return versions[0]  # Get the latest version
        else:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return None
        
    def get_item_name(self, item_id):

        language = "en_US"  # You can change this to another language if needed
        item_url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragonVersion}/data/{language}/item.json"

        response = requests.get(item_url)
        if response.status_code == 200:
            items_data = response.json()
            if str(item_id) in items_data["data"]:
                item_name = items_data["data"][str(item_id)]["name"]
                return item_name
            else:
                print(f"Error: Item with ID {item_id} not found")
                return None
        else:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return None    

    def get_match_data(self, game_id):
        url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/{game_id}?api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code == 200:
            # print(f"Got match data for game {game_id}:", response.json())
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return self.get_match_data(game_id)
        else:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return None
        
    def get_player_data(self, participant):
        itemNames = []
        for i in range(0, 7):
            if participant["item"+str(i)] != 0:
                itemNames.append(self.get_item_name(participant["item"+str(i)]))
        print(itemNames)
        print()
        
    def process_match_data(self, match_data):
        players = match_data["info"]["participants"]
        self.get_player_data(players[0])

    def process_all_games(self, games):
        for game in games:
            match_data = self.get_match_data(game)
            self.process_match_data(match_data)

    def main(self):
        #!!! issue: non-ranked games are not being filtered out
        #module testing
        cg = ChallengerGames()

        # Get challenger games from the past day
        games_past_day = cg.get_challenger_games_past_day()
        print("Challenger games in the past day:")
        self.process_all_games(games_past_day)


    
if __name__ == '__main__':
    processor = MatchData()
    processor.main()


        # Get the playerNameMap dictionary
        # player_name_map = cg.playerNameMap
        # print("Player Name Map:")
        # print(player_name_map)
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

