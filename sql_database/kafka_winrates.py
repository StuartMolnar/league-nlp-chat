from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from champion_winrates import ChampionWinrates

import logging
import logging.config
import yaml
from contextlib import contextmanager
from kafka_consumer import Consumer

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

    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.
        """
        logger.info('Start the Kafka consumer')
        consumer = Consumer(app_config['kafka']['topic_winrates'], self.__process_winrate)
        consumer.run_kafka_consumer()