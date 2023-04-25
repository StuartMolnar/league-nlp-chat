import requests
import time
import os
import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'


class ChallengerGames:
    def __init__(self):
        """
        Initialize the ChallengerGames object.

        Call get_challenger_players() to fetch the challenger players from the Riot Games API.

        Call the playerNameMap dict to get the player names used, mapped to their PUUID.
        """
        self.playerNameMap = {}

    def get_challenger_players(self):
        """
        Fetch the challenger players from the Riot Games API.

        Returns:
            list: A list of challenger players, or an empty list if there's an error.
        """
        url = f'https://{REGION[0]}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_KEY}'
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return []

        json_response = response.json()
        if 'entries' not in json_response:
            print(f"Error: 'entries' key not found in response JSON: {json_response}")
            return []

        return json_response['entries']

    def get_puuid(self, summoner_id):
        """
        Fetch the PUUID (Player Universally Unique ID) of a player by their summoner ID.

        Args:
            summoner_id (str): The summoner ID of the player.

        Returns:
            str: The player's PUUID, or None if there's an error.
        """
        url = f'https://{REGION[0]}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return None

        data = response.json()

        if 'puuid' not in data or 'name' not in data:
            print(f"Error: 'puuid' or 'name' key not found in response data: {data}")
            return None

        self.playerNameMap[data['puuid']] = data['name']
        return data['puuid']

    def get_recent_matches(self, puuid, start_time):
        """
        Fetch the recent matches of a player by their PUUID.

        Args:
            puuid (str): The PUUID of the player.
            start_time (int): The Unix timestamp to fetch matches from.

        Returns:
            list: A list of recent match IDs, or an empty list if there's an error.
        """
        url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=100&startTime={start_time}&api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return self.get_recent_matches(puuid, start_time)
        else:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return []

    def get_challenger_games_past_day(self):
        """
        Fetch the challenger games that occurred in the past day.

        Returns:
            list: A list of unique game IDs from the past day.
        """
        current_time = datetime.datetime.utcnow()
        one_day_ago = int((current_time - datetime.timedelta(days=1)).timestamp())
        challenger_players = self.get_challenger_players()
        unique_game_ids = set()

        for player in challenger_players:
            summoner_id = player['summonerId']
            puuid = self.get_puuid(summoner_id)
            recent_matches = self.get_recent_matches(puuid, one_day_ago)

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
    games_past_day = cg.get_challenger_games_past_day()
    print(games_past_day)
    print(cg.playerNameMap)


if __name__ == '__main__':
    main()
