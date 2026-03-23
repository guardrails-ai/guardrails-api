from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import JSONB
from guardrails_api.db.models.base import Base


class GuardItem(Base):
    __tablename__ = "guards"
    id = Column(String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    guard = Column(JSONB, nullable=False)
    created_by = Column(String, nullable=False, default="guardrails-api")
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_by = Column(String, nullable=False, default="guardrails-api")
    updated_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
