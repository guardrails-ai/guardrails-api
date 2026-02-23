from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from guardrails_api.db.models.base import Base


class GuardItem(Base):
    __tablename__ = "guards"
    id = Column(String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, unique=True, nullable=False)
    guard = Column(JSONB, nullable=False)
    created_by = Column(String, nullable=True, default="guardrails-api")
    created_at = Column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_by = Column(String, nullable=True, default="guardrails-api")
    updated_at = Column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP")
    )

    def __init__(self, id, name, guard, created_by, created_at, updated_by, updated_at):
        self.id = id
        self.name = name
        self.guard = guard
        self.created_by = created_by
        self.created_at = created_at
        self.updated_by = updated_by
        self.updated_at = updated_at
