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
    name: str
    champion: str
    role: str
    kills: int
    deaths: int
    assists: int
    items: list[str]

class ChallengerMatchupCreate(BaseModel):
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
    players = data['BOTTOM']
    player1 = players[0]
    player2 = players[1]
    



    matchup = ChallengerMatchup(
        player1_name=player1[0],
        player1_champion=player1[1],
        player1_role=player1[2],
        player1_kills=player1[3],
        player1_deaths=player1[4],
        player1_assists=player1[5],
        player1_items=player1[6],  # pass list directly
        player2_name=player2[0],
        player2_champion=player2[1],
        player2_role=player2[2],
        player2_kills=player2[3],
        player2_deaths=player2[4],
        player2_assists=player2[5],
        player2_items=player2[6]   # pass list directly
    )

    print('length 1', len(matchup.player1_items))
    print('length 2', len(matchup.player2_items))
    print('player1 items: ', matchup.player1_items)
    print('player2 items: ', matchup.player2_items)
    print('player 1 type: ', type(matchup.player1_items))
    print('player 2 type: ', type(matchup.player2_items))
    session = app_SESSION()
    session.add(matchup)
    session.commit()
    session.refresh(matchup)

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




# class PlayerData(BaseModel):
#     name: str
#     champion: str
#     role: str
#     kills: int
#     deaths: int
#     assists: int
#     items: list[str]

# class ChallengerMatchupCreate(BaseModel):
#     players: list[PlayerData]

# @app.on_event("startup")
# async def create_table():
#     table = ChallengerMatchup.__table__
#     async with Base.begin() as conn:
#         if not await Base.has_table(table.name):
#             create_table_query = CreateTable(table)
#             await conn.run_sync(conn.execute)(create_table_query)

# @app.post("/challenger-matchup/", response_model=int)
# async def create_matchup(data: ChallengerMatchupCreate):
#     matchup_id = await create_challenger_matchup(data.players)
#     return matchup_id

# @app.delete("/challenger-matchup/{id}")
# async def delete_matchup(id: int = Path(..., description="The ID of the challenger matchup to delete")):
#     return await delete_challenger_matchup(id)
