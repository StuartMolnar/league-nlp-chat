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
        self.playerNameMap = {}

    def get_challenger_players(self):
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
        url = f'https://{REGION[0]}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={RIOT_KEY}'
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: status code {response.status_code}, response content: {response.content}")
            return None

        data = response.json()

        if 'puuid' not in data or 'name' not in data:
            print(f"Error: 'puuid' or 'name' key not found in response data: {data}")
            return None

        self.playerNameMap[data['name']] = data['puuid']
        return data['puuid']

    def get_recent_matches(self, puuid, start_time):
        url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=100&startTime={start_time}&api_key={RIOT_KEY}'
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
            return ['error']

    def get_challenger_games_past_day(self):
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
    # module testing
    cg = ChallengerGames()
    games_past_day = cg.get_challenger_games_past_day()
    print(games_past_day)
    print(cg.playerNameMap)


if __name__ == '__main__':
    main()
