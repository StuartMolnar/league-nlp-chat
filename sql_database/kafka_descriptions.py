from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from base import Base
from rune_descriptions import RuneDescription

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

class DescriptionData(BaseModel):
    """
    Represents the data for a single rune description.
    """
    id: int
    tree: str
    name: str
    description: str

class KafkaDescriptions:
    """
    A class for consuming rune description messages from a Kafka topic and storing them in a database.

    Attributes:
        None

    Methods:
        run_kafka_consumer(): Runs the Kafka consumer in a separate thread.

    Usage:
        kafka_descriptions = KafkaDescriptions()
        
        kafka_descriptions.run_kafka_consumer()
    """
    def __init__(self):
        logger.info('Initialize the KafkaDescriptions object')

    def __process_description(self, description: DescriptionData):
        """
        Create a new rune description in the database.

        Args:
            description: A DescriptionData object containing the rune description.
        """
        try:
            with session_scope() as session:
                # Check if an entry with the same ID already exists
                existing_entry = session.query(RuneDescription).filter_by(name=description["name"]).one_or_none()

                if existing_entry:
                    # Update the existing entry
                    existing_entry.tree = description["rune_tree"]
                    existing_entry.name = description["name"]
                    existing_entry.description = description["long_desc"]
                    logger.info(f"Updated rune description with id: {existing_entry.id}")
                else:
                    # Create a new entry
                    new_entry = RuneDescription(
                        tree=description["rune_tree"],
                        name=description["name"],
                        description=description["long_desc"]
                    )
                    session.add(new_entry)
                    session.flush()
                    session.refresh(new_entry)
                    logger.info(f"Created rune description with id: {new_entry.id}")
        except ValueError as e:
            logger.error(f"Failed to parse rune description: {description}. Error: {e}")
        except Exception as e:
            logger.error(f"Failed to create rune description: {e}", exc_info=True)


    def run_kafka_consumer(self):
        """
        Run the Kafka consumer in a separate thread.
        """
        logger.info(f'Start the rune description Kafka consumer')
        consumer = Consumer(app_config['kafka']['topic_descriptions'], self.__process_description)
        consumer.run_kafka_consumer()