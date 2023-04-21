import requests
import time
import os
import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

RIOT_KEY = os.getenv("RIOT_KEY")
REGION = 'na1', 'americas'

def get_challenger_players():
    url = f'https://{REGION[0]}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_KEY}'
    response = requests.get(url)
    # print('got challenger players')
    return response.json()['entries']

def get_puuid(summoner_id):
    url = f'https://{REGION[0]}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={RIOT_KEY}'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: status code {response.status_code}, response content: {response.content}")
        return None
    
    data = response.json()
    
    if 'puuid' not in data:
        print(f"Error: 'puuid' key not found in response data: {data}")
        return None
    
    # print(f"Got puuid for summoner_id {summoner_id}: {data['puuid']}")
    return data['puuid']


def get_recent_matches(puuid, start_time):
    url = f'https://{REGION[1]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=100&startTime={start_time}&api_key={RIOT_KEY}'
    response = requests.get(url)
    # print('getting recent matches')

    if response.status_code == 200:
        # print('response 200:', response.content)
        return response.json()
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying.")
        time.sleep(retry_after)
        return get_recent_matches(puuid, start_time)
    else:
        print(f"Error: status code {response.status_code}, response content: {response.content}")
        return ['error']


def get_challenger_games_past_day():
    # Get the current time in UTC
    current_time = datetime.datetime.utcnow()

    # Calculate the timestamp for one week ago
    one_day_ago = int((current_time - datetime.timedelta(days=1)).timestamp())
    challenger_players = get_challenger_players()
    unique_game_ids = set()
    
    for player in challenger_players:
        summoner_id = player['summonerId']
        puuid = get_puuid(summoner_id)
        recent_matches = get_recent_matches(puuid, one_day_ago)

        for match in recent_matches:
            unique_game_ids.add(match)

    games_past_hour = list(unique_game_ids)
    return games_past_hour

challenger_games = get_challenger_games_past_day()
print(challenger_games)
