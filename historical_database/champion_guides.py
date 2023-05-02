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
    guide = Column(Text(20000))
    guide_hash = Column(String(64))

    __table_args__ = (UniqueConstraint('guide_hash', name='unique_guide'),)

    def __init__(self, guide):
        self.guide = guide
        self.guide_hash = hashlib.sha256(guide.encode('utf-8')).hexdigest()
