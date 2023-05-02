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
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from challenger_matchups import ChallengerMatchup

#--------------- add apache kafka ---------------
# in the challenger games service, use a kafka producer to store the data to a topic
# in this file, use a kafka consumer to consume the data from the topic and store it to our database
# may have to update the challenger games service to do all the data preparation logic (i.e. only send one matchup at a time to the producer - during data gathering) before sending it to the topic

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


app_ENGINE = create_engine(f"mysql+pymysql://{app_config['database']['username']}:{app_config['database']['password']}@{app_config['database']['hostname']}:{app_config['database']['port']}/{app_config['database']['name']}")
Base.metadata.bind = app_ENGINE
app_SESSION = sessionmaker(bind=app_ENGINE)

# app = FastAPI()

# # Allow CORS requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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

# implement get methods to retrieve the data from the database
# @app.exception_handler(Exception)
# async def handle_internal_server_error(request: Request, exc: Exception):
#     logger.exception(exc)
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"message": "Internal server error", "detail": str(exc)},
#     )


# app = FastAPI(exception_handlers={Exception: handle_internal_server_error})   



def process_matchup(players):
    #read the todo list up top
    """
    Create a new challenger matchup in the database.

    Args:
        data: A dictionary containing a single key-value pair,
              where the key is the role and the value is a list
              of two lists, each representing a player's data.

    Returns:
        The ID of the created matchup.
    """

    logger.info('Creating a new challenger matchup')
    
    player1 = players[0]
    player2 = players[1]

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
  
    session = app_SESSION()
    session.add(matchup)
    session.commit()
    session.refresh(matchup)

    logger.info(f"Created matchup object: {matchup}")

    return matchup.id

def consume_messages():
    """
    Consume messages from the Kafka topic and process them.

    This function creates a Kafka consumer and subscribes to the configured topic.
    The consumer is set up to deserialize the received messages from JSON format.
    It listens for new messages in the topic and calls the `process_matchup` function
    for each message to store the data in the database.
    """
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


if __name__ == "__main__":
    # Start the Kafka consumer in a separate thread
    kafka_consumer_thread = threading.Thread(target=consume_messages)
    kafka_consumer_thread.start()
    # uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

