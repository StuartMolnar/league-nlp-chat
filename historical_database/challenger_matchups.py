import json
from datetime import datetime
from typing import Any
from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from sqlalchemy.orm import Session
import logging
import logging.config
import yaml

from base import Base

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

class ChallengerMatchup(Base):
    __tablename__ = "challenger_matchups"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    player1_name = Column(String(50))
    player1_champion = Column(String(50))
    player1_kills = Column(Integer)
    player1_deaths = Column(Integer)
    player1_assists = Column(Integer)
    player1_items = Column(ARRAY(String(50)))  # store as list
    player1_role = Column(String(10))
    player2_name = Column(String(50))
    player2_champion = Column(String(50))
    player2_kills = Column(Integer)
    player2_deaths = Column(Integer)
    player2_assists = Column(Integer)
    player2_items = Column(ARRAY(String(50)))  # store as list
    player2_role = Column(String(10))

    def __init__(self, player1_name, player1_champion, player1_kills, player1_deaths, player1_assists, player1_items, player1_role, player2_name, player2_champion, player2_kills, player2_deaths, player2_assists, player2_items, player2_role):
        self.player1_name = player1_name
        self.player1_champion = player1_champion
        self.player1_kills = player1_kills
        self.player1_deaths = player1_deaths
        self.player1_assists = player1_assists
        self.player1_items = player1_items
        self.player1_role = player1_role
        self.player2_name = player2_name
        self.player2_champion = player2_champion
        self.player2_kills = player2_kills
        self.player2_deaths = player2_deaths
        self.player2_assists = player2_assists
        self.player2_items = player2_items
        self.player2_role = player2_role

