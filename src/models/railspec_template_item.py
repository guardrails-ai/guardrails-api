from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from src.models import db


class RailspecTemplateItem(db.Model):
    __tablename__ = "railspec_templates"
    owner = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    railspec = Column(JSONB, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)

    def __init__(self, owner, name, railspec, is_public):
        self.owner = owner
        self.name = name
        self.railspec = railspec
        self.is_public = is_public
