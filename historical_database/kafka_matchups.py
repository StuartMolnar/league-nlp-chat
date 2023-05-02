from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from challenger_matchups import ChallengerMatchup

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

class PlayerData(BaseModel):
    """
    Represents the data for a single player in a challenger matchup.
    """
    name: str
    champion: str
    role: str
    kills: int
    deaths: int
    assists: int
    items: list[str]

class ChallengerMatchupCreate(BaseModel):
    """
    Represents the data for a challenger matchup, including both players.
    """
    players: list[list[PlayerData]]


class KafkaMatchups:
    """
    A class for consuming challenger matchup messages from a Kafka topic and storing them in a database.

    Attributes:
        None

    Methods:
        process_matchup(players): Stores a challenger matchup in the database.
        consume_messages(): Consumes messages from a Kafka topic and processes them.
        run_kafka_consumer(): Runs the Kafka consumer in a separate thread.

    Usage:
        kafka_matchups = KafkaMatchups()
        
        kafka_matchups.run_kafka_consumer()
    """
    def __init__(self):
        logger.info('Initialize the KafkaMatchups object')

    def process_matchup(self, players):
        """
        Create a new challenger matchup in the database.

        Args:
            data: A dictionary containing a single key-value pair,
                where the key is the role and the value is a list
                of two lists, each representing a player's data.

        """
        logger.info('Creating a new challenger matchup')    
        player1 = players[0]
        player2 = players[1]

        try:
            with session_scope() as session:
                matchup = ChallengerMatchup(
                    player1_name=player1[0],
                    player1_champion=player1[1],
                    player1_role=player1[2],
                    player1_kills=player1[3],
                    player1_deaths=player1[4],
                    player1_assists=player1[5],
                    player1_items=json.dumps(player1[6]), # Serialize player items as a JSON string before storing them in the database
                    player2_name=player2[0],
                    player2_champion=player2[1],
                    player2_role=player2[2],
                    player2_kills=player2[3],
                    player2_deaths=player2[4],
                    player2_assists=player2[5],
                    player2_items=json.dumps(player2[6]) # Serialize player items as a JSON string before storing them in the database
                )
            
                session.add(matchup)
                session.flush() 
                session.refresh(matchup)

                logger.info(f"Created matchup object: {matchup}")
        except Exception as e:
            logger.error(f"Failed to create matchup object: {e}", exc_info=True)

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
                topic=app_config['kafka']['topic_matchups'],
                bootstrap_servers=app_config['kafka']['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='matchups_group',
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