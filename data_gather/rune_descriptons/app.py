import yaml
import logging
import logging.config
from ddragon_runes import DDragonRunes

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

kafka_topic = app_config['kafka']['topic']

if __name__ == '__main__':
    ddr = DDragonRunes()
    ddr.produce_rune_data(kafka_topic)