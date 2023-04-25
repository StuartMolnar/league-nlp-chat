import requests
import time
import os
import json
import datetime
from dotenv import load_dotenv
from challenger_games import ChallengerGames
import logging
import logging.config
import yaml

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'

class MatchData:
    def __init__(self):
        """
        Initialize the MatchData object.

        Fetches the latest game data version from the Data Dragon API and initializes
        the gameDataFiltered attribute as an empty list.
        """
        logger.info("MatchData object initialized")
        self.ddragonVersion = self.get_latest_ddragon_version()
        self.gameDataFiltered = []

    def get_latest_ddragon_version(self):
        """
        Fetch the latest game data version from the Data Dragon API.
        
        Returns:
            str: The latest version as a string, or None if there's an error.
        """
        logger.info("Fetching the latest Data Dragon version")
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        if response.status_code == 200:
            versions = response.json()
            return versions[0]  # Get the latest version
        else:
            logger.error(f"Status code {response.status_code}, response content: {response.content}")
            return None
        
    def get_item_name_by_id(self, item_id):
        """
        Get the name of the in-game item by its ID.

        Args:
            item_id (int): The ID of the item to fetch the name for.

        Returns:
            str: The item's name as a string, or None if there's an error.
        """
        logger.info(f"Fetching item name for item ID: {item_id}")
        language = "en_US"  # You can change this to another language if needed
        item_url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragonVersion}/data/{language}/item.json"

        response = requests.get(item_url)
        if response.status_code == 200:
            items_data = response.json()
            if str(item_id) in items_data["data"]:
                item_name = items_data["data"][str(item_id)]["name"]
                return item_name
            else:
                logger.info(f"Item with ID {item_id} not found")
                return None
        else:
            logger.error(f"Status code {response.status_code}, response content: {response.content}")
            return     

    def fetch_match_data_by_game_id(self, game_id):
        """
        Fetch match data for a specific game ID from the Riot Games API.

        Args:
            game_id (str): The ID of the game to fetch match data for.

        Returns:
            dict: The match data as a JSON object, or None if there's an error.
        """
        logger.info(f"Fetching match data for game ID: {game_id}")
        url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/{game_id}?api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            logger.info(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return self.fetch_match_data_by_game_id(game_id)
        else:
            logger.warning(f"Status code {response.status_code}, response content: {response.content}")
            return None        
            
    def extract_unique_team_positions(self, players):        
        """
        Extract unique team positions from a list of player dictionaries.

        Args:
            players (list): A list of player dictionaries containing team position information.

        Returns:
            set: A set of unique team positions.
        """
        logger.info("Extracting unique team positions")
        unique_positions = set()
        for player in players:
            unique_positions.add(player["teamPosition"])
        return unique_positions
    
    def extract_player_data_from_participant(self, participant):
        """
        Extracts and returns relevant player data from the participant dictionary.

        Args:
            participant (dict): A dictionary containing the participant's match data.

        Returns:
            list: A list containing the player's summoner name, champion name, team position,
                kills, deaths, assists, and item names.
        """
        logger.info("Extracting player data from participant")
        dataToGrab = ["summonerName", "championName", "teamPosition", "kills", "deaths", "assists"]
        data = []
        itemsToGrab = ["item0", "item1", "item2", "item3", "item4", "item5", "item6"]
        items = []
        for item in itemsToGrab:
            items.append(self.get_item_name_by_id(participant[item]))
        for data_item in dataToGrab:
            data.append(participant[data_item])

        player_data = data + items
        return player_data

    def group_players_by_position(self, players):
        """
        Pairs players by their team position and returns a dictionary of compositions.

        Args:
            players (list): A list of dictionaries containing player match data.

        Returns:
            dict: A dictionary with keys as team positions and values as lists of
                player data for each team position.
        """
        logger.info("Grouping players by position")
        unique_positions = self.extract_unique_team_positions(players)
        versus_compositions = {position: [] for position in unique_positions}

        for i in range(len(players)):
            team_position = players[i]["teamPosition"]

            if team_position in versus_compositions:
                data = self.extract_player_data_from_participant(players[i])
                versus_compositions[team_position].append(data)

        return versus_compositions
        
    def process_single_match_data(self, match_data):
        """
        Process match data to extract and pair player data by team position.

        Args:
            match_data (dict): A dictionary containing the match data.

        Returns:
            dict: A dictionary with keys as team positions and values as lists of
                player data for each team position.
        """
        logger.info("Processing single match data")
        players = match_data["info"]["participants"]
        return self.group_players_by_position(players)

    def process_all_games(self, games):
        """
        Process a list of games, extracting and pairing player data by team position.

        Args:
            games (list): A list of game IDs.

        Returns:
            list: A list of dictionaries, each containing player data paired by team position.
        """
        logger.info("Processing all games")
        processed_games = []
        for game in games:
            match_data = self.fetch_match_data_by_game_id(game)
            processed_games.append(self.process_single_match_data(match_data))

        return processed_games

    def fetch_challenger_data(self):
        """
        Fetch and process match data for challenger games from the past day.

        Returns:
            list: A list of dictionaries, each containing player data paired by team position.
        """
        logger.info("Fetching challenger match data")
        cg = ChallengerGames()
        games = cg.fetch_challenger_games_from_past_day()
        return self.process_all_games(games)

def main():
    #!!! todo, finish process all games function
    # prepare data for use in historical database service
    # set up main file that will run the modules and send data to the database service


    #module testing
    # cg = ChallengerGames()

    # Get challenger games from the past day
    # games_past_day = cg.get_challenger_games_past_day()
    games_past_day = ['NA1_4638633595', 'NA1_4638619939', 'NA1_4638740278', 'NA1_4638454797', 'NA1_4638500101', 'NA1_4638732418', 'NA1_4638622740', 'NA1_4638582501', 'NA1_4638655280', 'NA1_4638478680', 'NA1_4638810106', 'NA1_4638526935', 'NA1_4638568573', 'NA1_4638390819', 'NA1_4638799303', 'NA1_4638640572', 'NA1_4638625289', 'NA1_4638389920', 'NA1_4638547789', 'NA1_4638542108', 'NA1_4638453528', 'NA1_4638677124', 'NA1_4638485235', 'NA1_4638668657', 'NA1_4638769187', 'NA1_4638679608', 'NA1_4638662477', 'NA1_4638714098', 'NA1_4638621892', 'NA1_4638631866', 'NA1_4638689177', 'NA1_4638566386', 'NA1_4638629556', 'NA1_4638850853', 'NA1_4638501707', 'NA1_4638786771', 'NA1_4638398551', 'NA1_4638677565', 'NA1_4638544648', 'NA1_4638638258', 'NA1_4638680652', 'NA1_4638649249', 'NA1_4638611224', 'NA1_4638561991', 'NA1_4638732992', 'NA1_4638792285', 'NA1_4638802503', 'NA1_4638721939', 'NA1_4638558263', 'NA1_4638714749', 'NA1_4638650254', 'NA1_4638581458', 'NA1_4638380080', 'NA1_4638874515', 'NA1_4638627196']
    # print("Challenger games in the past day:")
    
    # process_all_games(games_past_day)



    
if __name__ == '__main__':
    data = MatchData()
    data.main()


        # Get the playerNameMap dictionary
        # player_name_map = cg.playerNameMap
        # print("Player Name Map:")
        # print(player_name_map)


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

