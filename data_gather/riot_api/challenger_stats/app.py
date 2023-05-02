import requests
import json
from challenger_match_data import MatchData
import logging
import logging.config
import yaml
from kafka import KafkaConsumer

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


if __name__ == '__main__':
    md = MatchData()
    challenger_data = md.produce_challenger_data()
    
    # add code to run this daily and add any necessary error handling
