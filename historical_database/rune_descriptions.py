from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from base import Base

class RuneDescription(Base):
    """
    A class representing a rune description in League of Legends.
    """
    __tablename__ = "rune_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tree = Column(String(50))
    name = Column(String(50))
    description = Column(String(1000))

    __table_args__ = (UniqueConstraint(
        'name', name='unique_description'),)

    def __init__(self, tree, name, description):
        self.tree = tree
        self.name = name
        self.description = description

