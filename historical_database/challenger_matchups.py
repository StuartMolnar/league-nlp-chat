from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from base import Base

class ChallengerMatchup(Base):
    """
    A class representing a challenger matchup in a League of Legends game.
    """
    __tablename__ = "challenger_matchups"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    player1_name = Column(String(50))
    player1_champion = Column(String(50))
    player1_kills = Column(Integer)
    player1_deaths = Column(Integer)
    player1_assists = Column(Integer)
    player1_items = Column(String(255))  # store as delimited string
    player1_role = Column(String(10))
    player2_name = Column(String(50))
    player2_champion = Column(String(50))
    player2_kills = Column(Integer)
    player2_deaths = Column(Integer)
    player2_assists = Column(Integer)
    player2_items = Column(String(255))  # store as delimited string
    player2_role = Column(String(10))


    __table_args__ = (UniqueConstraint(
        'player1_name', 'player1_champion', 'player1_kills', 'player1_deaths', 'player1_assists',
        'player1_items', 'player1_role', 'player2_name', 'player2_champion', 'player2_kills',
        'player2_deaths', 'player2_assists', 'player2_items', 'player2_role', name='unique_matchup'),)

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

