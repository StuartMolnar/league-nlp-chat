"""
This module provides API endpoints to manage league of legends data.
"""
from fastapi import FastAPI, HTTPException, Response
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
from kafka_winrates import KafkaWinrate, ChampionWinrates
from datetime import datetime, timezone, timedelta

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

app = FastAPI()

@app.exception_handler(Exception)
async def handle_internal_server_error(request, exc):
    """
    Handle internal server errors and log the exception.

    This function logs the exception and returns an appropriate JSON response
    with a 500 Internal Server Error status code.

    Args:
        request (Request): The request that caused the exception.
        exc (Exception): The exception that was raised.

    Returns:
        Response: A response with a 500 Internal Server Error status code,
                  and a content containing the error message and exception details.
    """
    logger.exception(exc)
    return Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
        media_type="application/json",
    )

app = FastAPI(exception_handlers={500: handle_internal_server_error}) 

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# add guides by id and matchups by id endpoints

@app.get("/matchups_past_day")
async def get_all_matchups_past_day():
    """
    Retrieve all challenger matchups from the database that were created in the past 24 hours.

    Returns:
        list: A list of challenger matchups, where each matchup contains data for both players.
    """
    logger.info("Retrieving all challenger matchups from the database")

    try:
        with session_scope() as session:
            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)

            matchups = session.query(ChallengerMatchup).filter(
                ChallengerMatchup.timestamp >= yesterday
            ).all()

            results = [
                {
                    "id": matchup.id,
                    "player1": {
                        "name": matchup.player1_name,
                        "champion": matchup.player1_champion,
                        "role": matchup.player1_role,
                        "kills": matchup.player1_kills,
                        "deaths": matchup.player1_deaths,
                        "assists": matchup.player1_assists,
                        "items": matchup.player1_items
                    },
                    "player2": {
                        "name": matchup.player2_name,
                        "champion": matchup.player2_champion,
                        "role": matchup.player2_role,
                        "kills": matchup.player2_kills,
                        "deaths": matchup.player2_deaths,
                        "assists": matchup.player2_assists,
                        "items": matchup.player2_items
                    },
                    "date": matchup.timestamp.strftime('%B %d')
                    
                }
                for matchup in matchups
            ]
            logger.info(f"Retrieved {len(results)} matchups from the database")
            return results

    except Exception as e:
        logger.error(f"Failed to retrieve matchups: {e}", exc_info=True)
        raise e
    
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
            matchups = session.query(ChallengerMatchup).all()

            results = [
                {
                    "id": matchup.id,
                    "player1": {
                        "name": matchup.player1_name,
                        "champion": matchup.player1_champion,
                        "role": matchup.player1_role,
                        "kills": matchup.player1_kills,
                        "deaths": matchup.player1_deaths,
                        "assists": matchup.player1_assists,
                        "items": matchup.player1_items
                    },
                    "player2": {
                        "name": matchup.player2_name,
                        "champion": matchup.player2_champion,
                        "role": matchup.player2_role,
                        "kills": matchup.player2_kills,
                        "deaths": matchup.player2_deaths,
                        "assists": matchup.player2_assists,
                        "items": matchup.player2_items
                    },
                    "date": matchup.timestamp.strftime('%B %d')
                }
                for matchup in matchups
            ]
            logger.info(f"Retrieved {len(results)} matchups from the database")
            return results

    except Exception as e:
        logger.error(f"Failed to retrieve matchups: {e}", exc_info=True)
        raise e
    
@app.get("/guides")
async def get_all_guides():
    """
    Retrieve all champion guides from the database.

    Returns:
        list: A list of champion guides, where each entry is a list containing the champion name and guide text.
    """
    logger.info("Retrieving all champion guides from the database")

    try:
        with session_scope() as session:
            guides = session.query(ChampionGuide).all()
            formatted_guides = [{"id": row.id, "champion": row.champion, "guide": row.guide} for row in guides]
            return formatted_guides
    except Exception as e:
        logger.error(f"Failed to retrieve guides: {e}", exc_info=True)
        raise e
    
@app.get("/guides/{id}")
async def get_guide_by_id(id: int):
    """
    Retrieve a champion guide from the database by its ID.

    Args:
        id (int): The ID of the guide to retrieve.

    Returns:
        dict: A dictionary containing the champion name and guide text.
    """
    logger.info(f"Retrieving guide with ID {id} from the database")

    try:
        with session_scope() as session:
            guide = session.query(ChampionGuide).filter(ChampionGuide.id == id).first()
            return {"id": guide.id, "champion": guide.champion, "guide": guide.guide}
    except Exception as e:
        logger.error(f"Failed to retrieve guide with ID {id}: {e}", exc_info=True)
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
                {"id": rune_desc.id, "tree": rune_desc.tree, "name": rune_desc.name, "description": rune_desc.description}
                for rune_desc in rune_descriptions
            ]
    except Exception as e:
        logger.error(f"Failed to retrieve rune descriptions: {e}", exc_info=True)
        raise e

@app.get("/rune_descriptions/{id}")
async def get_rune_description_by_id(id: int):
    """
    Retrieve a specific rune description from the database by its ID.

    Args:
        rune_id (int): The ID of the rune description.

    Returns:
        dict: A dictionary containing information on the specified rune description.
    """
    logger.info(f"Retrieving rune description with ID {id} from the database")

    try:
        with session_scope() as session:
            rune_desc = session.query(RuneDescription).filter(RuneDescription.id == id).first()
            if rune_desc is not None:
                return {
                    "id": rune_desc.id,
                    "tree": rune_desc.tree,
                    "name": rune_desc.name,
                    "description": rune_desc.description
                }
            else:
                raise HTTPException(status_code=404, detail=f"Rune description with ID {id} not found")
    except Exception as e:
        logger.error(f"Failed to retrieve rune description with ID {id}: {e}", exc_info=True)
        raise e
    
@app.get("/top_runes")
async def get_all_top_runes():
    """
    Retrieve all champion runes from the database.

    Returns:
        list: A list of champion runes, where each entry is a list containing information on a rune.
    """
    logger.info("Retrieving all champion runes from the database")

    try:
        with session_scope() as session:
            top_runes = session.query(TopRunes).all()
            return [
                {"id": row.id, "champion": row.champion, "runes": row.runes}
                for row in top_runes
            ]
    except Exception as e:
        logger.error(f"Failed to retrieve champion runes: {e}", exc_info=True)
        raise e
    
@app.get("/top_runes/{id}")
async def get_top_runes_by_champion(id: int):
    """
    Retrieve champion runes for a specific champion from the database.

    Args:
        champion_name (str): The name of the champion for which to retrieve runes.

    Returns:
        list: A list containing information on the runes for the specified champion.
    """
    logger.info(f"Retrieving runes for champion id '{id}' from the database")

    try:
        with session_scope() as session:
            top_runes = session.query(TopRunes).filter_by(id=id).one_or_none()
            if top_runes:
                return {"id": top_runes.id, "champion": top_runes.champion, "runes": top_runes.runes}
            else:
                return {"message": f"No runes found for champion '{top_runes.champion}'"}
    except Exception as e:
        logger.error(f"Failed to retrieve runes for champion: {e}", exc_info=True)
        raise e


@app.get("/winrates")
async def get_all_winrates():
    """
    Retrieve all champion winrates from the database.

    Returns:
        list: A list of champion winrates, where each entry is a list containing information on a winrate.
    """
    logger.info("Retrieving all champion winrates from the database")

    try:
        with session_scope() as session:
            champion_winrates = session.query(ChampionWinrates).all()
            return [
                {"id": row.id, "champion": row.champion, "winrate": row.winrate}
                for row in champion_winrates
            ]
    except Exception as e:
        logger.error(f"Failed to retrieve Kafka winrates: {e}", exc_info=True)
        raise e

@app.get("/winrates/{id}")
async def get_winrate_by_champion(id: int):
    """
    Retrieve champion winrate for a specific champion from the database.

    Args:
        champion_name (str): The name of the champion for which to retrieve winrate.

    Returns:
        list: A list containing information on the winrate for the specified champion.
    """
    logger.info(f"Retrieving champion winrate for champion id '{id}' from the database")

    try:
        with session_scope() as session:
            champion_winrate = session.query(ChampionWinrates).filter_by(id=id).one_or_none()
            if champion_winrate:
                return {"id": champion_winrate.id, "champion": champion_winrate.champion, "winrate": champion_winrate.winrate}
            else:
                return {"message": f"No winrate found for champion '{champion_winrate.champion}'"}
    except Exception as e:
        logger.error(f"Failed to retrieve winrate for champion': {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    # # Start the Kafka matchups consumer
    kafka_matchup = KafkaMatchups()
    kafka_matchup.run_kafka_consumer()

    # Start the Kafka guides consumer
    kafka_guide = KafkaGuides()
    kafka_guide.run_kafka_consumer()

    # # Start the rune descriptions consumer
    rune_descriptions = KafkaDescriptions()
    rune_descriptions.run_kafka_consumer()

    # Start the top runes consumer
    top_runes = KafkaRunes()
    top_runes.run_kafka_consumer()

    # Start the winrate consumer
    winrates = KafkaWinrate()
    winrates.run_kafka_consumer()

    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

