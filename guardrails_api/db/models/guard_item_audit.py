from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, CHAR
from guardrails_api.db.models.base import Base


class GuardItemAudit(Base):
    __tablename__ = "guards_audit"
    id = Column(String, primary_key=True)
    guard_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    guard = Column(JSONB, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    replaced_on = Column(TIMESTAMP, nullable=False)
    operation = Column(CHAR, nullable=False)
