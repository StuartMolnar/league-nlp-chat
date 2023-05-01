import requests
import json
from challenger_match_data import MatchData
import logging
import logging.config
import yaml

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


if __name__ == '__main__':
    md = MatchData()
    challenger_data = md.fetch_challenger_data()
    

    url = "http://localhost:8000/challenger-matchup/"
    logger.debug('---------------- running main ----------------')
    # logger.debug('------------challenger data: %s', challenger_data)

    for data_dict in challenger_data:
        logger.info(f"Sending match data to {url}")
        for key, value in data_dict.items():
            payload = {key: value}
            response = requests.post(url, json=payload)

            if response.status_code == 200:
                logger.info(f"Data sent successfully, received ID: {response.json()}")
            else:
                logger.error(f"Failed to send data: {response.status_code}, {response.text}")
