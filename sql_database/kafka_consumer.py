from kafka.errors import NoBrokersAvailable
import json
import logging
import logging.config
import yaml
from kafka import KafkaConsumer
import threading
import time

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

class Consumer:
    def __init__(self, topic, process_function):
        self.topic = topic
        self.process_function = process_function

    def __consume_messages(self):
            """
            Consume messages from the Kafka topic and process them.

            This function creates a Kafka consumer and subscribes to the configured topic.
            The consumer is set up to deserialize the received messages from JSON format.
            It listens for new messages in the topic and calls the `process_function` function
            for each message to store the data in the database.
            """
            attempts = 0
            while attempts < 5:
                try:
                    logger.info('Consuming messages from kafka topic')
                    consumer = KafkaConsumer(
                        self.topic,
                        bootstrap_servers=app_config['kafka']['bootstrap_servers'],
                        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                        auto_offset_reset='latest',
                        enable_auto_commit=True,
                        group_id='consumer_group',
                        max_poll_interval_ms=1000,
                        max_poll_records=20,
                    )
                    break
                except NoBrokersAvailable:
                    logger.error("Kafka broker not available, retrying in 10 seconds", exc_info=True)
                    attempts += 1
                    time.sleep(10)

            for message in consumer:
                try:
                    message_data = message.value
                    if not isinstance(message_data, dict):
                        raise TypeError("Message is not a dictionary")

                    if message_data:
                        self.process_function(message_data)
                    else:
                        logger.warning('Received an empty message, skipping')
                except TypeError as e:
                    logger.error(f"Message is not a dictionary: {e}")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON: {e}", exc_info=True)
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing message: {e}", exc_info=True)
                    continue

    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.

        This function creates a new thread for the Kafka consumer and starts it.
        The consumer listens for new messages in the configured Kafka topic and processes
        them using the `process_function` method.
        """
        kafka_consumer_thread = threading.Thread(target=self.__consume_messages)
        kafka_consumer_thread.daemon = True
        kafka_consumer_thread.start()