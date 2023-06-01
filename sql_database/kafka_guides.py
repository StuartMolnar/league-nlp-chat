from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from base import Base
from champion_guides import ChampionGuide
from kafka_consumer import Consumer

import logging
import logging.config
import yaml
from truncating_log_handler import TruncatingLogHandler
from contextlib import contextmanager

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
    except IntegrityError as e:
        session.rollback()
        logger.error(f"IntegrityError occurred: {e}", exc_info=True)
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise
    finally:
        session.close()

class GuideData(BaseModel):
    """
    Represents the data for a single champion guide.
    """
    champion: str
    guide: str


class KafkaGuides:
    """
    A class for consuming champion guide messages from a Kafka topic and storing them in a database.

    Attributes:
        None

    Methods:
        run_kafka_consumer(): Runs the Kafka consumer in a separate thread.

    Usage:
        kafka_guides = KafkaGuides()
        
        kafka_guides.run_kafka_consumer()
    """
    def __init__(self):
        logger.info('Initialize the KafkaGuides object')

    def __process_guide(self, guide_data: GuideData):
        """
        Create a new champion guide in the database.

        Args:
            guide_data: A GuideData object containing the champion name and guide text.
        """
        try:
            with session_scope() as session:
                # Check if an entry with the same champion already exists
                existing_guide = session.query(ChampionGuide).filter_by(champion=guide_data.champion).one_or_none()

                if existing_guide:
                    # Update the existing entry
                    existing_guide.guide = guide_data.guide
                    logger.info(f"Updated guide object for champion: {existing_guide.champion}")
                else:
                    # Create a new entry
                    guide = ChampionGuide(
                        champion=guide_data.champion,
                        guide=guide_data.guide
                    )
                    session.add(guide)
                    session.flush()
                    session.refresh(guide)
                    logger.info(f"Created guide object at id: {guide.id}")
        except Exception as e:
            logger.error(f"Failed to create guide object: {e}", exc_info=True)

    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.
        """
        logger.info(f'Start the guides Kafka consumer')
        consumer = Consumer(app_config['kafka']['topic_guides'], self.__process_guide)
        consumer.run_kafka_consumer()