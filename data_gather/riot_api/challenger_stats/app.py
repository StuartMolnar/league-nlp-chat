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

def consume_messages(topic, bootstrap_servers):
    logger.debug('Consuming messages...')
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='matchups_group',
    )

    logger.debug(f"Consuming messages from topic '{topic}':")
    for message in consumer:
        logger.debug(f"Received message: {message.value}")

if __name__ == '__main__':
    md = MatchData()
    challenger_data = md.produce_challenger_data()
    #testing
    consume_messages('challenger_matchups', ['localhost:9092'])
    
    # add code to run this daily and add any necessary error handling'
    # create an endpoint in the database service that will run code to consume the challenger_matchups topic and add it to the database
    # run the challenger data code, then call the database endpoint
