from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from src.models.base import db


class GuardItem(db.Model):
    __tablename__ = "guards"
    # TODO: Make primary key a composite between guard.name and the guard owner's userId
    name = Column(String, primary_key=True)
    railspec = Column(JSONB, nullable=False)
    num_reasks = Column(Integer, nullable=True)
    # owner = Column(String, nullable=False)

    def __init__(
        self,
        name,
        railspec,
        num_reasks
        # owner = None
    ):
        self.name = name
        self.railspec = railspec
        self.num_reasks = num_reasks
        # self.owner = owner
