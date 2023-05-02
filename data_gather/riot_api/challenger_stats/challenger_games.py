import requests
import time
import os
import datetime
from dotenv import load_dotenv
import logging
import logging.config
import yaml

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Load environment variables from the .env file
load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'


class ChallengerGames:
    def __init__(self):
        """
        Initialize the ChallengerGames object.

        Call fetch_challenger_games_from_past_day() to fetch the challenger games from the Riot Games API.
        """
        logger.info("ChallengerGames object initialized")

    def __fetch_challenger_players(self):
        """
        Fetch the challenger players from the Riot Games API.

        Returns:
            list: A list of challenger players, or an empty list if there's an error.
        """
        logger.info("Fetching challenger players...")
        url = f'https://{REGION[0]}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_KEY}'
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.error(f"Status code {response.status_code}, response content: {response.content}")
            return []

        json_response = response.json()
        if 'entries' not in json_response:
            logger.error(f"'entries' key not found in response JSON: {json_response}")
            return []

        return json_response['entries']

    def __fetch_puuid_by_summoner_id(self, summoner_id):
        """
        Fetch the PUUID (Player Universally Unique ID) of a player by their summoner ID.

        Args:
            summoner_id (str): The summoner ID of the player.

        Returns:
            str: The player's PUUID, or None if there's an error.
        """
        logger.info(f"Fetching PUUID for summoner ID: {summoner_id}")
        url = f'https://{REGION[0]}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code != 200:
            logger.warning(f"Status code {response.status_code}, response content: {response.content}")
            return None

        data = response.json()

        if 'puuid' not in data or 'name' not in data:
            logger.error(f"'puuid' or 'name' key not found in response data: {data}")
            return None

        return data['puuid']

    def __fetch_recent_matches_by_puuid(self, puuid, start_time):
        """
        Fetch the recent matches of a player by their PUUID.

        Args:
            puuid (str): The PUUID of the player.
            start_time (int): The Unix timestamp to fetch matches from.

        Returns:
            list: A list of recent match IDs, or an empty list if there's an error.
        """
        logger.info(f"Fetching recent matches for PUUID: {puuid}")
        url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=100&startTime={start_time}&api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            logger.info(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return self.__fetch_recent_matches_by_puuid(puuid, start_time)
        else:
            logger.warning(f"Status code {response.status_code}, response content: {response.content}")
            return []

    def fetch_challenger_games_from_past_day(self):
        """
        Fetch the challenger games that occurred in the past day.

        Returns:
            list: A list of unique game IDs from the past day.
        """
        logger.info("Fetching challenger match data")
        current_time = datetime.datetime.utcnow()
        one_day_ago = int((current_time - datetime.timedelta(days=1)).timestamp())
        challenger_players = self.__fetch_challenger_players()
        unique_game_ids = set()

        for player in challenger_players:
            summoner_id = player['summonerId']
            puuid = self.__fetch_puuid_by_summoner_id(summoner_id)
            recent_matches = self.__fetch_recent_matches_by_puuid(puuid, one_day_ago)

            for match in recent_matches:
                unique_game_ids.add(match)

        games_past_day = list(unique_game_ids)
        return games_past_day

def main():
    """
    The main function for testing the ChallengerGames module.
    Fetches challenger games from the past day and prints the game IDs and player name map.
    """
    cg = ChallengerGames()
    games_past_day = cg.fetch_challenger_games_from_past_day()
    print(games_past_day)


if __name__ == '__main__':
    main()
