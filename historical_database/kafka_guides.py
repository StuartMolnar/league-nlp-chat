from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from champion_guides import ChampionGuide

import logging
import logging.config
import yaml
import json
from kafka import KafkaConsumer
from contextlib import contextmanager
import threading

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


app_ENGINE = create_engine(f"mysql+pymysql://{app_config['database']['username']}:{app_config['database']['password']}@{app_config['database']['hostname']}:{app_config['database']['port']}/{app_config['database']['name']}")
Base.metadata.bind = app_ENGINE
app_SESSION = sessionmaker(bind=app_ENGINE)

@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.

    This context manager creates a new SQLAlchemy session, handles
    committing or rolling back transactions based on the success or
    failure of the operations within the context, and automatically
    closes the session when the context is exited.

    Usage:
        with session_scope() as session:
            # Perform database operations using the session

    Yields:
        session (Session): An instance of a SQLAlchemy session for
                           executing database operations.
    """
    session = app_SESSION()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class GuideData(BaseModel):
    """
    Represents the data for a single champion guide.
    """
    guide: str

class KafkaGuides:
    def __init__(self):
        logger.info('Initialize the KafkaGuides object')

    def process_matchup(self, guide: GuideData):
        

        try:
            with session_scope() as session:
                guide = ChampionGuide(
                    guide=guide
                )
                session.add(guide)
                session.flush() 
                session.refresh(guide)

                logger.info(f"Created guide object: {guide}")
        except Exception as e:
            logger.error(f"Failed to create guide object: {e}", exc_info=True)

    def consume_messages(self):
        """
        Consume messages from the Kafka topic and process them.

        This function creates a Kafka consumer and subscribes to the configured topic.
        The consumer is set up to deserialize the received messages from JSON format.
        It listens for new messages in the topic and calls the `process_matchup` function
        for each message to store the data in the database.
        """
        try:
            logger.info('Consuming messages from kafka topic')
            consumer = KafkaConsumer(
                topic=app_config['kafka']['topic_guides'],
                bootstrap_servers=app_config['kafka']['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='guides_group',
            )

            for message in consumer:
                self.process_matchup(message.value)

        except Exception as e:
            logger.error(f"Error consuming messages: {e}", exc_info=True)

    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.
        """
        kafka_consumer_thread = threading.Thread(target=self.consume_messages)
        kafka_consumer_thread.start()