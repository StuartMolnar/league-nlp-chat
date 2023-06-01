from kafka import KafkaConsumer
import json
import logging
import logging.config
import yaml
from truncating_log_handler import TruncatingLogHandler

try:
    with open('log_conf.yml', 'r') as f:
        log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
except (FileNotFoundError, yaml.YAMLError) as e:
    print(f"Error loading logging configuration: {e}")

logger = logging.getLogger('basicLogger')

def consume_messages():
    topic = 'rune_descriptions'
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id=f'{topic}_consumer_group',
    )

    for message in consumer:
        logger.info(f"Received message: {message.value}")

if __name__ == "__main__":
    consume_messages()

