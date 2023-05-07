"""
This module provides API endpoints to manage league of legends data.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import logging.config
import yaml
import json
from truncating_log_handler import TruncatingLogHandler
from datetime import datetime, timezone
from kafka_matchups import session_scope, KafkaMatchups, ChallengerMatchup
from kafka_guides import KafkaGuides, ChampionGuide
from kafka_descriptions import KafkaDescriptions, RuneDescription
from kafka_runes import KafkaRunes, TopRunes

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

app = FastAPI()

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

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/matchups")
async def get_all_matchups():
    """
    Retrieve all challenger matchups from the database that were created on the same UTC day as the request.

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

            results = [
                [
                    [matchup.player1_name, matchup.player1_champion, matchup.player1_role, matchup.player1_kills, matchup.player1_deaths, matchup.player1_assists, matchup.player1_items],
                    [matchup.player2_name, matchup.player2_champion, matchup.player2_role, matchup.player2_kills, matchup.player2_deaths, matchup.player2_assists, matchup.player2_items]
                ]
                for matchup in matchups
            ]

            return results

    except Exception as e:
        logger.error(f"Failed to retrieve matchups: {e}", exc_info=True)
        raise e
    
@app.get("/guides")
async def get_all_guides():
    """
    Retrieve all champion guides from the database.

    Returns:
        list: A list of champion guides, where each guide contains a text block.
    """
    logger.info("Retrieving all champion guides from the database")

    try:
        with session_scope() as session:
            today = datetime.now(timezone.utc).date()  # Get the current date in UTC timezone
            guides = session.query(ChampionGuide.guide).filter(
                ChampionGuide.timestamp >= today  # Filter by created_at date
            ).all()
            return guides
    except Exception as e:
        logger.error(f"Failed to retrieve guides: {e}", exc_info=True)
        raise e

@app.get("/rune_descriptions")
async def get_all_rune_descriptions():
    """
    Retrieve all rune descriptions from the database.

    Returns:
        list: A list of rune descriptions, where each description is a list containing information on a rune.
    """
    logger.info("Retrieving all rune descriptions from the database")

    try:
        with session_scope() as session:
            rune_descriptions = session.query(RuneDescription).all()
            return [
                [rune_desc.id, rune_desc.tree, rune_desc.name, rune_desc.description]
                for rune_desc in rune_descriptions
            ]
    except Exception as e:
        logger.error(f"Failed to retrieve rune descriptions: {e}", exc_info=True)
        raise e

@app.get("/rune_descriptions/{rune_id}")
async def get_rune_description_by_id(rune_id: int):
    """
    Retrieve a specific rune description from the database by its ID.

    Args:
        rune_id (int): The ID of the rune description.

    Returns:
        dict: A dictionary containing information on the specified rune description.
    """
    logger.info(f"Retrieving rune description with ID {rune_id} from the database")

    try:
        with session_scope() as session:
            rune_desc = session.query(RuneDescription).filter(RuneDescription.id == rune_id).first()
            if rune_desc is not None:
                return {
                    "id": rune_desc.id,
                    "tree": rune_desc.tree,
                    "name": rune_desc.name,
                    "description": rune_desc.description
                }
            else:
                raise HTTPException(status_code=404, detail=f"Rune description with ID {rune_id} not found")
    except Exception as e:
        logger.error(f"Failed to retrieve rune description with ID {rune_id}: {e}", exc_info=True)
        raise e
    
if __name__ == "__main__":
    # # Start the Kafka matchups consumer
    # kafka_matchup = KafkaMatchups()
    # kafka_matchup.run_kafka_consumer()

    # Start the Kafka guides consumer
    kafka_guide = KafkaGuides()
    kafka_guide.run_kafka_consumer()

    # # Start the rune descriptions consumer
    # rune_descriptions = KafkaDescriptions()
    # rune_descriptions.run_kafka_consumer()

    # Start the top runes consumer
    # top_runes = KafkaRunes()
    # top_runes.run_kafka_consumer()

    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

