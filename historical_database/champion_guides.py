from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, UniqueConstraint
import hashlib

from base import Base

class ChampionGuide(Base):
    """
    A class representing a character guide for a League of Legends champion.
    """
    __tablename__ = "champion_guides"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    champion = Column(String(100))
    guide = Column(Text(20000))

    __table_args__ = (UniqueConstraint('champion', name='unique_guide'),)

    def __init__(self, champion, guide):
        self.champion = champion
        self.guide = guide
