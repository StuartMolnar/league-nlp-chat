import requests
import time
import os
from dotenv import load_dotenv
from challenger_games import ChallengerGames
import logging
import logging.config
import yaml
from kafka import KafkaProducer
import json

# Initialize the Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Load the configuration files
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'

class MatchData:
    """
    A class to fetch and filter match data from the Riot API and send it to a Kafka topic.

    Attributes:
        ddragonVersion (str): The latest game data version from the Data Dragon API.
        gameDataFiltered (list): A list of filtered game data after processing.

    Methods:
        produce_challenger_data: Fetches and processes match data for challenger games and sends the compositions to a Kafka topic.

    Usage:
        match_data = MatchData()
        
        match_data.produce_challenger_data(topic)
    """
    def __init__(self):
        """
        Initialize the MatchData object.

        Fetches the latest game data version from the Data Dragon API and initializes
        the gameDataFiltered attribute as an empty list.

        Call the fetch_challenger_data method to fetch the latest challenger match data.
        """
        logger.info("MatchData object initialized")
        self.ddragonVersion = self.__get_latest_ddragon_version()
        self.gameDataFiltered = []

    def __get_latest_ddragon_version(self):
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
            return versions[0]  # Latest version
        else:
            logger.error(f"Status code {response.status_code}, response content: {response.content}")
            return None
        
    def __get_item_name_by_id(self, item_id):
        """
        Get the name of the in-game item by its ID.

        Args:
            item_id (int): The ID of the item to fetch the name for.

        Returns:
            str: The item's name as a string, or None if there's an error.
        """
        # logger.debug(f"Fetching item name for item ID: {item_id}")
        language = "en_US"
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

    def __fetch_match_data_by_game_id(self, game_id):
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
            return self.__fetch_match_data_by_game_id(game_id)
        else:
            logger.warning(f"Status code {response.status_code}, response content: {response.content}")
            return None        
            
    def __extract_unique_team_positions(self, players):        
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
    
    def __extract_player_data_from_participant(self, participant):
        """
        Extracts and returns relevant player data from the participant dictionary.

        Args:
            participant (dict): A dictionary containing the participant's match data.

        Returns:
            list: A list containing the player's summoner name, champion name, team position,
                kills, deaths, assists, and item names.
        """
        logger.info("Extracting player data from participant")
        fieldsToGrab = ["summonerName", "championName", "teamPosition", "kills", "deaths", "assists"]
        fields = []
        itemsToGrab = ["item0", "item1", "item2", "item3", "item4", "item5", "item6"]
        items = []
        for field in fieldsToGrab:
            try:
                if field == "teamPosition":
                    team_position = participant[field][0] + participant[field][1:].lower()
                    if team_position == "Utility":
                        team_position = "Support"
                    fields.append(team_position)
                else:
                    fields.append(participant[field])
            except Exception as e:
                logger.error(f"Error extracting {field} from participant: {e}")
                logger.debug(f"Participant: {participant}")
                logger.debug(f"Field [0]: {participant[field][0]}")

        for item in itemsToGrab:
            item_name = self.__get_item_name_by_id(participant[item])
            if item_name != None:
                items.append(item_name)

        perks = []
        if "perks" in participant and "styles" in participant["perks"]:
            for style in participant["perks"]["styles"]:
                if "selections" in style:
                    for selection in style["selections"]:
                        if "perk" in selection:
                            perks.append(selection["perk"])

        player_data = fields + [items] + [perks]

        return player_data
    
    def __send_compositions_to_kafka(self, versus_compositions, topic):
        """
        Sends each composition in the versus_compositions data structure to a Kafka topic.

        Args:
            versus_compositions (dict): A dictionary with keys as team positions and values as lists of player data for each team position.
            topic (str): The name of the Kafka topic to send the data to.
        """
        logger.info("Sending matchups to Kafka")
        for composition in versus_compositions.items():
            composition = composition[-1] # Get the list of player data from the tuple
            producer.send(topic, composition)
            logger.debug(f"Sent matchup data to Kafka topic '{topic}': {composition}")

        producer.flush()


    def __group_players_by_position(self, players, topic):
        """
        Pairs players by their team position and returns a dictionary of compositions.

        Args:
            players (list): A list of dictionaries containing player match data.

        Returns:
            dict: A dictionary with keys as team positions and values as lists of
                player data for each team position.
        """
        logger.info("Grouping players by position")
        unique_positions = self.__extract_unique_team_positions(players)
        versus_compositions = {position: [] for position in unique_positions}

        for i in range(len(players)):
            team_position = players[i]["teamPosition"]
            if team_position == '':
                logger.info(f"Player {players[i]['summonerName']} has no team position. Skipping match.")
                return

            if team_position in versus_compositions:
                data = self.__extract_player_data_from_participant(players[i])
                logger.debug(f"Player data: {data}")
                versus_compositions[team_position].append(data)
        
        self.__send_compositions_to_kafka(versus_compositions, topic)
        
    def __process_single_match_data(self, match_data, topic):
        """
        Process match data to extract and pair player data by team position.

        Args:
            match_data (dict): A dictionary containing the match data.

        """
        logger.info("Processing single match data")
        players = match_data["info"]["participants"]
        self.__group_players_by_position(players, topic)

    def __process_all_games(self, games, topic):
        """
        Process a list of games, extracting and pairing player data by team position,
        and sending the compositions to a Kafka topic.

        Args:
            games (list): A list of game IDs.
        """
        logger.info("Processing all games")
        for game in games:
            logger.info(f"Processing game: {game}")
            match_data = self.__fetch_match_data_by_game_id(game)
            self.__process_single_match_data(match_data, topic)
        

    def produce_challenger_data(self, topic):
        """
        Fetch and process match data for challenger games from the past day,
        and send the compositions to a Kafka topic.
        """
        cg = ChallengerGames()
        games = cg.fetch_challenger_games_from_past_day()
        self.__process_all_games(games, topic)
        logger.info("Finished sending all games")
    
if __name__ == '__main__':
    pass
