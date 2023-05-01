"""
This module provides API endpoints to manage league of legends data.
"""
from fastapi import FastAPI, Path, Request
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import logging.config
import yaml
from typing import List, Dict, Any
import json


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from challenger_matchups import ChallengerMatchup

#--------------- add apache kafka ---------------

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
async def handle_internal_server_error(request: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
    )


app = FastAPI(exception_handlers={Exception: handle_internal_server_error})   

@app.post("/challenger-matchup/", response_model=int)
async def create_matchup(data: Dict[str, List[List[Any]]]):
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
    
    players = next(iter(data.values())) # Extract the first value from the dictionary regardless of the key
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

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

