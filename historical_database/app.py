"""
This module provides API endpoints to manage league of legends data.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import logging.config
import yaml
import json
from kafka import KafkaConsumer
from datetime import datetime, timezone
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from challenger_matchups import ChallengerMatchup

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


app_ENGINE = create_engine(f"mysql+pymysql://{app_config['database']['username']}:{app_config['database']['password']}@{app_config['database']['hostname']}:{app_config['database']['port']}/{app_config['database']['name']}")
Base.metadata.bind = app_ENGINE
app_SESSION = sessionmaker(bind=app_ENGINE)

app = FastAPI()

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.exception_handler(Exception)
async def handle_internal_server_error(exc: Exception):
    """
    Handle internal server errors and log the exception.

    This function logs the exception and returns an appropriate JSON response
    with a 500 Internal Server Error status code.

    Args:
        exc (Exception): The exception that was raised.

    Returns:
        JSONResponse: A JSON response with a 500 Internal Server Error status code,
                      and a content containing the error message and exception details.
    """
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
    )
app = FastAPI(exception_handlers={Exception: handle_internal_server_error})  

@app.get("/matchups")
async def get_all_matchups():
    """
    Retrieve all challenger matchups from the database that were created on the same day as the request.

    Returns:
        list: A list of challenger matchups, where each matchup contains data for both players.
    """
    logger.info("Retrieving all challenger matchups from the database")

    try:
        with session_scope() as session:
            today = datetime.now(timezone.utc).date()  # Get the current date in UTC timezone
            matchups = session.query(ChallengerMatchup).filter(
                ChallengerMatchup.timestamp >= today  # Filter by created_at date
            ).all()

            results = []
            for matchup in matchups:
                # Deserialize player items from JSON string before returning the data
                player1_items = json.loads(matchup.player1_items)
                player2_items = json.loads(matchup.player2_items)

                result = {
                    "players": [
                        [matchup.player1_name, matchup.player1_champion, matchup.player1_role, matchup.player1_kills, matchup.player1_deaths, matchup.player1_assists, player1_items],
                        [matchup.player2_name, matchup.player2_champion, matchup.player2_role, matchup.player2_kills, matchup.player2_deaths, matchup.player2_assists, player2_items]
                    ]
                }
                results.append(result)

            return results

    except Exception as e:
        logger.error(f"Failed to retrieve matchups: {e}", exc_info=True)
        raise e



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

def process_matchup(players):
    #read the todo list up top
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

def consume_messages():
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
            app_config['kafka']['topic'],
            bootstrap_servers=app_config['kafka']['bootstrap_servers'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='matchups_group',
        )

        for message in consumer:
            process_matchup(message.value)

    except Exception as e:
        logger.error(f"Error consuming messages: {e}", exc_info=True)


if __name__ == "__main__":
    # Start the Kafka consumer in a separate thread
    # kafka_consumer_thread = threading.Thread(target=consume_messages)
    # kafka_consumer_thread.start()
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

