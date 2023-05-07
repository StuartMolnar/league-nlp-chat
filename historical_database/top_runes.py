from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, UniqueConstraint
import hashlib

from base import Base

class TopRunes(Base):
    """
    A class representing the top runes for a League of Legends champion.
    """
    __tablename__ = "top_runes"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    champion = Column(String(100))
    runes = Column(String(500))

    __table_args__ = (UniqueConstraint('champion', name='unique_guide'),)

    def __init__(self, champion, runes):
        self.champion = champion
        self.runes = runes
