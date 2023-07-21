from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from src.models.base import db


class RailspecTemplateItem(db.Model):
    __tablename__ = "railspec_templates"
    owner = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    railspec = Column(JSONB, nullable=False)

    def __init__(
        self,
        owner,
        name,
        railspec
    ):
        self.owner = owner
        self.name = name
        self.railspec = railspec
