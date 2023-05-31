import logging
import logging.config
import yaml
import requests
from typing import Callable, Dict, List, Tuple, Union

try:
    with open('log_conf.yml', 'r') as f:
        log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
except (FileNotFoundError, yaml.YAMLError) as e:
    print(f"Error loading logging configuration: {e}")

logger = logging.getLogger('basicLogger')

try:
    with open('app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())
except (FileNotFoundError, yaml.YAMLError) as e:
    logger.error(f"Error loading application configuration: {e}")
    raise

endpoint = app_config.get('endpoints', {}).get('database', '')

ProcessingFunc = Callable[[Dict[str, Union[str, int]]], Tuple[str, str]]

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
        self.processing_funcs: Dict[str, ProcessingFunc] = {
            'matchups': self.__process_matchup_string,
            'guides': self.__process_guide_string,
            'winrates': self.__process_winrate_string,
            'rune_descriptions': self.__process_rune_description_string,
            'top_runes': self.__process_top_rune_string,
        }

    @staticmethod
    def __process_matchup_string(matchup: Dict[str, Union[str, int]]) -> Tuple[str, str]:
        """
        Processes and formats a matchup string.

        Args:
            matchup (dict): A dictionary containing information about a matchup.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the matchup.
        """
        if isinstance(matchup, dict) and 'player1' in matchup:
            items = matchup['player1'].get('items', '').split('| ')
            items = ', '.join(items)
            matchup_string = f"on {matchup.get('date', '')}, {matchup['player1'].get('name', '')} played {matchup['player1'].get('champion', '')} {matchup['player1'].get('role', '')} versus {matchup['player2'].get('champion', '')}, he went {matchup['player1'].get('kills', '')}-{matchup['player1'].get('deaths', '')}-{matchup['player1'].get('assists', '')} and built {items}" 
            return matchup_string, matchup.get('id', '')
        return '', ''
    
    @staticmethod
    def __process_guide_string(guide: Dict[str, Union[str, int]]) -> Tuple[str, str]:
        """
        Processes and formats a guide string.

        Args:
            guide (dict): A dictionary containing information about a guide.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the guide.
        """
        if isinstance(guide, dict):
            guide_string = f"This is a {guide.get('champion', '')} guide: {guide.get('guide', '')}"
            return guide_string, guide.get('id', '')
        return '', ''
    
    @staticmethod
    def __process_winrate_string(winrate: Dict[str, Union[str, int]]) -> Tuple[str, str]:        
        """
        Processes and formats a winrate string.

        Args:
            winrate (dict): A dictionary containing information about a champion's winrate.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the winrate.
        """
        if isinstance(winrate, dict):
            winrate_string = f"{winrate.get('champion', '')} has a winrate of {winrate.get('winrate', '')}"
            return winrate_string, winrate.get('id', '')
        return '', ''
    
    @staticmethod
    def __process_rune_description_string(rune_description: Dict[str, Union[str, int]]) -> Tuple[str, str]:        
        """
        Processes and formats a rune description string.

        Args:
            rune_description (dict): A dictionary containing information about a rune.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the rune.
        """
        if isinstance(rune_description, dict):
            rune_description_string = f"{rune_description.get('name', '')} is a {rune_description.get('tree', '')} rune, description: {rune_description.get('description', '')}"
            return rune_description_string, rune_description.get('id', '')
        return '', ''
    
    @staticmethod
    def __process_top_rune_string(top_rune: Dict[str, Union[str, int]]) -> Tuple[str, str]:
        """
        Processes and formats a top rune string.

        Args:
            top_rune (dict): A dictionary containing information about a champion's top runes.

        Returns:
            tuple: A tuple where the first element is the processed string and the second element is the ID of the top rune.
        """
        if isinstance(top_rune, dict):
            top_rune_string = f"The top runes for {top_rune.get('champion', '')} are: {top_rune.get('runes', '')}"
            return top_rune_string, top_rune.get('id', '')
        return '', ''
    
    def prepare_service(self, service: str) -> Union[List[Tuple[str, str]], None]:
        url = endpoint + service
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            return
        except requests.exceptions.RequestException as e:
            logger.error(f"Error occurred: {e}")
            return
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return

        if service in self.processing_funcs:
            return [self.processing_funcs[service](item) for item in data if isinstance(item, dict)]
        else:
            logger.error(f'Unsupported service: {service}')
    
    