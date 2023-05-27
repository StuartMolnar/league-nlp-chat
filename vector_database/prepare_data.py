import logging
import logging.config
import yaml
import requests

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

endpoint = app_config['endpoints']['database']

class PrepareData:
    """
    A class for preparing data fetched from different services. 

    Attributes:
        processing_funcs (dict): A dictionary mapping service names to their respective processing functions.

    Methods:
        prepare_service(service): Fetches and prepares data for a specific service.
    """
    def __init__(self):
        """
        Initializes the PrepareData instance.
        
        Initializes the processing_funcs dictionary with service names as keys and their processing functions as values.
        """
        self.processing_funcs = {
            'matchups': self.__process_matchup_string,
            'guides': self.__process_guide_string,
            'winrates': self.__process_winrate_string,
            'rune_descriptions': self.__process_rune_description_string,
            'top_runes': self.__process_top_rune_string,
        }

    @staticmethod
    def __process_matchup_string(matchup):
        """
        Processes and formats a matchup string.

        Args:
            matchup (dict): A dictionary containing information about a matchup.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the matchup.
        """
        matchup_string = ''
        items = matchup['player1']['items'].split('| ')
        items = ', '.join(items)

        matchup_string = f"on {matchup['date']}, {matchup['player1']['name']} played {matchup['player1']['champion']} {matchup['player1']['role']} versus {matchup['player2']['champion']}, he went {matchup['player1']['kills']}-{matchup['player1']['deaths']}-{matchup['player1']['assists']} and built {items}" 

        return matchup_string, matchup['id']
    
    @staticmethod
    def __process_guide_string(guide):
        """
        Processes and formats a guide string.

        Args:
            guide (dict): A dictionary containing information about a guide.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the guide.
        """
        guide_string = f"This is a {guide['champion']} guide: {guide['guide']}"
        return guide_string, guide['id']
    
    @staticmethod
    def __process_winrate_string(winrate):
        """
        Processes and formats a winrate string.

        Args:
            winrate (dict): A dictionary containing information about a champion's winrate.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the winrate.
        """
        winrate_string = f"{winrate['champion']} has a winrate of {winrate['winrate']}"
        return winrate_string, winrate['id']
    
    @staticmethod
    def __process_rune_description_string(rune_description):
        """
        Processes and formats a rune description string.

        Args:
            rune_description (dict): A dictionary containing information about a rune.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the rune.
        """
        rune_description_string = f"{rune_description['name']} is a {rune_description['tree']} rune, description: {rune_description['description']}"
        return rune_description_string, rune_description['id']
    
    @staticmethod
    def __process_top_rune_string(top_rune):
        """
        Processes and formats a top rune string.

        Args:
            top_rune (dict): A dictionary containing information about a champion's top runes.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the top rune.
        """
        top_rune_string = f"The top runes for {top_rune['champion']} are: {top_rune['runes']}"
        return top_rune_string, top_rune['id']
    
    def prepare_service(self, service):
        """
        Fetches and prepares data for a specified service.

        Args:
            service (str): The name of the service to be processed.

        Returns:
            list: A list of processed data items for the service, where each item is a tuple containing a processed string and an ID. Returns None if there's an error.
        """
        url = endpoint + service
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            logger.error(f'Failed to request {service} data: {response.status_code}')
            return

        if service in self.processing_funcs:
            return [self.processing_funcs[service](item) for item in data]
        else:
            logger.error(f'Unsupported service: {service}')
    
    