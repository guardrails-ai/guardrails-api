from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, CHAR
from guardrails_api.models.base import Base


class GuardItemAudit(Base):
    __tablename__ = "guards_audit"
    id = Column(String, primary_key=True)
    guard_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    guard = Column(JSONB, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    replaced_on = Column(TIMESTAMP, nullable=False)
    operation = Column(CHAR, nullable=False)

    def __init__(
        self,
        id,
        guard_id,
        name,
        guard,
        created_by,
        created_at,
        updated_by,
        updated_at,
        replaced_on,
        operation,
    ):
        self.id = id
        self.guard_id = guard_id
        self.name = name
        self.guard = guard
        self.created_by = created_by
        self.created_at = created_at
        self.updated_by = updated_by
        self.updated_at = updated_at
        self.replaced_on = replaced_on
        self.operation = operation
