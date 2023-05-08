import logging
import logging.config
import yaml
import requests

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

challenger_matchups_url = 'http://localhost:8000/matchups'
champion_guides_url = 'http://localhost:8000/guides'
champion_winrates_url = 'http://localhost:8000/champion_winrates/'
rune_descriptions_url = 'http://localhost:8000/rune_descriptions/'
top_runes_url = 'http://localhost:8000/top_runes/'

def prepare_matchups():
    """
    Prepares the matchups data for vector embedding.
    """
    response = requests.get(challenger_matchups_url)
    matchups = response.json()
    if response.status_code != 200:
        logger.error(f'Failed to request matchups data: {response.status_code}')
        return
    
    def prepare_matchup_string(matchup):
        matchup_string = ''
        items_string = ''
        items = matchup['player1']['items'].split('| ')
        items = ', '.join(items)

        matchup_string = f"{matchup['player1']['name']} recently played {matchup['player1']['champion']} {matchup['player1']['role']} versus {matchup['player2']['champion']}, he went {matchup['player1']['kills']}-{matchup['player1']['deaths']}-{matchup['player1']['assists']} and built {items}" 

        return matchup_string
    
    for matchup in matchups:
        logger.info(prepare_matchup_string(matchup))

#prepare_matchups()

def prepare_guides():
    """
    Prepares the guides data for vector embedding.
    """
    response = requests.get(champion_guides_url)
    guides = response.json()
    if response.status_code != 200:
        logger.error(f'Failed to request guides data: {response.status_code}')
        return
    
    def prepare_guide_string(guide):
        guide_string = f"This is a {guide['champion']} guide, here is the text: {guide['guide']}"
        return guide_string
    
    for guide in guides:
        logger.info(prepare_guide_string(guide))

#prepare_guides()

def prepare_winrates():
    """
    Prepares the winrates data for vector embedding.
    """
    response = requests.get(champion_winrates_url)
    winrates = response.json()
    if response.status_code != 200:
        logger.error(f'Failed to request winrates data: {response.status_code}')
        return
    
    def prepare_winrate_string(winrate):
        winrate_string = f"{winrate['champion']} currently has a winrate of {winrate['winrate']}"
        return winrate_string
    
    for winrate in winrates:
        logger.info(prepare_winrate_string(winrate))

#prepare_winrates()

def prepare_rune_descriptions():
    """
    Prepares the rune descriptions data for vector embedding.
    """
    response = requests.get(rune_descriptions_url)
    rune_descriptions = response.json()
    if response.status_code != 200:
        logger.error(f'Failed to request rune descriptions data: {response.status_code}')
        return
    
    def prepare_rune_description_string(rune_description):
        rune_description_string = f"{rune_description['name']} is a {rune_description['tree']} rune, here is the description: {rune_description['description']}"
        return rune_description_string
    
    for rune_description in rune_descriptions:
        logger.info(prepare_rune_description_string(rune_description))

#prepare_rune_descriptions()

def prepare_top_runes():
    """
    Prepares the top runes data for vector embedding.
    """
    response = requests.get(top_runes_url)
    top_runes = response.json()
    if response.status_code != 200:
        logger.error(f'Failed to request top runes data: {response.status_code}')
        return
    
    def prepare_top_rune_string(top_rune):
        top_rune_string = f"The top runes for {top_rune['champion']} are: {top_rune['runes']}"
        return top_rune_string
    
    for top_rune in top_runes:
        logger.info(prepare_top_rune_string(top_rune))

prepare_top_runes()