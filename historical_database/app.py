"""
This module provides API endpoints to manage league of legends data.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import logging.config
import yaml
import json
from datetime import datetime, timezone
from kafka_matchups import session_scope, KafkaMatchups, ChallengerMatchup
from kafka_guides import session_scope, KafkaGuides, ChampionGuide

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

app = FastAPI()

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
@app.get("/guides")
async def get_all_matchups():
    """
    Retrieve all champion guides from the database that were created on the same day as the request.

    Returns:
        list: A list of champion guides, where each matchup contains a text block.
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
    
if __name__ == "__main__":
    # Start the Kafka matchups consumer
    kafka_matchup = KafkaMatchups()
    kafka_matchup.run_kafka_consumer()

    # Start the Kafka guides consumer
    kafka_guide = KafkaGuides()
    kafka_guide.run_kafka_consumer()

    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

