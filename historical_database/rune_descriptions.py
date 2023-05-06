from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from base import Base

class RuneDescription(Base):
    """
    A class representing a challenger matchup in a League of Legends game.
    """
    __tablename__ = "rune_de"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tree = Column(String(50))
    name = Column(String(50))
    description = Column(String(1000))


    __table_args__ = (UniqueConstraint(
        'id', name='unique_matchup'),)

    def __init__(self, id, tree, name, description):
        self.id = id
        self.tree = tree
        self.name = name
        self.description = description

