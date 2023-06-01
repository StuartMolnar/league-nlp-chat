from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from top_runes import TopRunes

import logging
import logging.config
import yaml
from contextlib import contextmanager
from kafka_consumer import Consumer
from truncating_log_handler import TruncatingLogHandler

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

class RuneData(BaseModel):
    """
    Represents the data for a single champion top runes list.
    """
    champion: str
    runes: str

class KafkaRunes:
    """
    A class for consuming champion top runes messages from a Kafka topic and storing them in a database.

    Attributes:
        None

    Methods:
        run_kafka_consumer(): Runs the Kafka consumer in a separate thread.

    Usage:
        kafka_runes = KafkaRunes()
        
        kafka_runes.run_kafka_consumer()
    """
    def __init__(self):
        logger.info('Initialize the KafkaRunes object')

    def __process_runes(self, rune_data: RuneData):
        """
        Create a new top runes list in the database.

        Args:
            guide: A RuneData object containing the runes list.
        """
        try:
            with session_scope() as session:
                # Check if an entry with the same champion already exists
                existing_runes = session.query(TopRunes).filter_by(champion=rune_data.champion).one_or_none()

                if existing_runes:
                    # Update the existing entry
                    existing_runes.runes = rune_data.runes
                    logger.info(f"Updated runes object for champion: {existing_runes.champion}")
                else:
                    # Create a new entry
                    runes = TopRunes(
                        champion=rune_data.champion,
                        runes=rune_data.runes
                    )
                    session.add(runes)
                    session.flush()
                    session.refresh(runes)
                    logger.info(f"Created runes object at id: {runes.id}")
        except Exception as e:
            logger.error(f"Failed to create runes object: {e}", exc_info=True)

    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.
        """
        logger.info(f'Start the runes Kafka consumer')
        consumer = Consumer(app_config['kafka']['topic_runes'], self.__process_runes)
        consumer.run_kafka_consumer()