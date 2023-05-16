from challenger_match_data import MatchData
import logging
import logging.config
import yaml
from truncating_log_handler import TruncatingLogHandler


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

kafka_topic = app_config['kafka']['topic']

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

if __name__ == '__main__':
    md = MatchData()
    challenger_data = md.produce_challenger_data(kafka_topic)
    
    # add code to run this daily and add any necessary error handling
