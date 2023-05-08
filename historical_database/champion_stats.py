from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint

from base import Base

class ChampStats(Base):
    """
    A class representing the top runes for a League of Legends champion.
    """
    __tablename__ = "champion_stats"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    champion = Column(String(100))
    winrate = Column(String(6))

    __table_args__ = (UniqueConstraint('champion', name='unique_champion'),)

    def __init__(self, champion, winrate):
        self.champion = champion
        self.winrate = winrate