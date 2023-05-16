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

class PrepareData:
    def prepare_matchups(self):
        """
        Prepares the matchups data for vector embedding.
        """
        response = requests.get(challenger_matchups_url)
        matchups = response.json()
        if response.status_code != 200:
            logger.error(f'Failed to request matchups data: {response.status_code}')
            return
        
        def __process_matchup_string(matchup):
            matchup_string = ''
            items = matchup['player1']['items'].split('| ')
            items = ', '.join(items)

            matchup_string = f"on {matchup['date']}, {matchup['player1']['name']} played {matchup['player1']['champion']} {matchup['player1']['role']} versus {matchup['player2']['champion']}, he went {matchup['player1']['kills']}-{matchup['player1']['deaths']}-{matchup['player1']['assists']} and built {items}" 

            return matchup_string, matchup['id']
        
        return [__process_matchup_string(matchup) for matchup in matchups]

            

    def prepare_guides(self):
        """
        Prepares the guides data for vector embedding.
        """
        response = requests.get(champion_guides_url)
        guides = response.json()
        if response.status_code != 200:
            logger.error(f'Failed to request guides data: {response.status_code}')
            return
        
        def __process_guide_string(guide):
            guide_string = f"This is a {guide['champion']} guide: {guide['guide']}"
            return guide_string, guide['id']
        
        return [__process_guide_string(guide) for guide in guides]

    def prepare_winrates(self):
        """
        Prepares the winrates data for vector embedding.
        """
        response = requests.get(champion_winrates_url)
        winrates = response.json()
        if response.status_code != 200:
            logger.error(f'Failed to request winrates data: {response.status_code}')
            return
        
        def __process_winrate_string(winrate):
            winrate_string = f"{winrate['champion']} has a winrate of {winrate['winrate']}"
            return winrate_string, winrate['id']
        
        return [__process_winrate_string(winrate) for winrate in winrates]

    def prepare_rune_descriptions(self):
        """
        Prepares the rune descriptions data for vector embedding.
        """
        response = requests.get(rune_descriptions_url)
        rune_descriptions = response.json()
        if response.status_code != 200:
            logger.error(f'Failed to request rune descriptions data: {response.status_code}')
            return
        
        def __process_rune_description_string(rune_description):
            rune_description_string = f"{rune_description['name']} is a {rune_description['tree']} rune, description: {rune_description['description']}"
            return rune_description_string, rune_description['id']
        
        return [__process_rune_description_string(rune_description) for rune_description in rune_descriptions]


    def prepare_top_runes(self):
        """
        Prepares the top runes data for vector embedding.
        """
        response = requests.get(top_runes_url)
        top_runes = response.json()
        if response.status_code != 200:
            logger.error(f'Failed to request top runes data: {response.status_code}')
            return
        
        def __process_top_rune_string(top_rune):
            top_rune_string = f"The top runes for {top_rune['champion']} are: {top_rune['runes']}"
            return top_rune_string, top_rune['id']
        
        return [__process_top_rune_string(top_rune) for top_rune in top_runes]


    
# data_prep = PrepareData()
# matchups = data_prep.prepare_matchups()
# logger.info(f'matchups data: {(matchups)}')
