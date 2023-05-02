from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from base import Base

class ChampionGuide(Base):
    __tablename__ = "champion_guides"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    build = Column(String(20000))

    def __init__(self, guide):
        self.guide = guide

