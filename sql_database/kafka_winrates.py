from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from champion_winrates import ChampionWinrates

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

class WinrateData(BaseModel):
    """
    Represents the winrate data for a single champion.
    """
    champion: str
    winrate: str

class KafkaWinrate:
    """
    A class for consuming champion winrate messages from a Kafka topic and storing them in a database.

    Attributes:
        None

    Methods:
        run_kafka_consumer(): Runs the Kafka consumer in a separate thread.

    Usage:
        kafka_winrate = KafkaWinrate()
        
        kafka_winrate.run_kafka_consumer()
    """
    def __init__(self):
        logger.info('Initialize the KafkaWinrate object')

    def __process_winrate(self, winrate_data: WinrateData):
        """
        Create a new champion winrate in the database.

        Args:
            guide: A WinrateData object containing the runes list.
        """
        try:
            with session_scope() as session:
                # Check if an entry with the same champion already exists
                existing_entry = session.query(ChampionWinrates).filter_by(champion=winrate_data.champion).one_or_none()

                if existing_entry:
                    # Update the existing entry
                    existing_entry.winrate = winrate_data.winrate
                    logger.info(f"Updated winrate object for champion: {existing_entry.champion}")
                else:
                    # Create a new entry
                    champ_winrate = ChampionWinrates(
                        champion=winrate_data.champion,
                        winrate=winrate_data.winrate
                    )
                    session.add(champ_winrate)
                    session.flush()
                    session.refresh(champ_winrate)
                    logger.info(f"Created winrate object for champion: {champ_winrate.champion}")
        except Exception as e:
            logger.error(f"Failed to create winrate object: {e}", exc_info=True)

    def __consume_messages(self):
        """
        Consume messages from the Kafka topic and process them.

        This function creates a Kafka consumer and subscribes to the configured topic.
        The consumer is set up to deserialize the received messages from JSON format.
        It listens for new messages in the topic and calls the `__process_winrate` function
        for each message to store the data in the database.
        """
        try:
            logger.info('Consuming messages from kafka topic')
            consumer = KafkaConsumer(
                app_config['kafka']['topic_winrate'],
                bootstrap_servers=app_config['kafka']['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='winrate_group',
                max_poll_interval_ms=1000,
                max_poll_records=20,
            )
            for message in consumer:
                rune_data = WinrateData(**message.value)
                self.__process_winrate(rune_data)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}", exc_info=True)


    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.

        This function creates a new thread for the Kafka consumer and starts it.
        The consumer listens for new messages in the configured Kafka topic and processes
        them using the `process_runes` method.
        """
        kafka_consumer_thread = threading.Thread(target=self.__consume_messages)
        kafka_consumer_thread.daemon = True
        kafka_consumer_thread.start()