from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, CHAR
from guardrails_api.models.base import db


class GuardItemAudit(db.Model):
    __tablename__ = "guards_audit"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    railspec = Column(JSONB, nullable=False)
    num_reasks = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    # owner = Column(String, nullable=False)
    replaced_on = Column(TIMESTAMP, nullable=False)
    # replaced_by = Column(String, nullable=False)
    operation = Column(CHAR, nullable=False)

    def __init__(
        self,
        id,
        name,
        railspec,
        num_reasks,
        description,
        # owner = None
        replaced_on,
        # replaced_by
        operation,
    ):
        self.id = id
        self.name = name
        self.railspec = railspec
        self.num_reasks = num_reasks
        self.description = description
        self.replaced_on = replaced_on
        self.operation = operation
        # self.owner = owner


AUDIT_FUNCTION = """
CREATE OR REPLACE FUNCTION guard_audit_function() RETURNS TRIGGER AS $guard_audit$
BEGIN
    IF (TG_OP = 'DELETE') THEN
    INSERT INTO guards_audit SELECT uuid_generate_v4(), OLD.*, now(), 'D';
    ELSIF (TG_OP = 'UPDATE') THEN
    INSERT INTO guards_audit SELECT uuid_generate_v4(), OLD.*, now(), 'U';
    ELSIF (TG_OP = 'INSERT') THEN
    INSERT INTO guards_audit SELECT uuid_generate_v4(), NEW.*, now(), 'I';
    END IF;
    RETURN null;
END;
$guard_audit$
LANGUAGE plpgsql;
"""

AUDIT_TRIGGER = """
DROP TRIGGER IF EXISTS guard_audit_trigger
  ON guards;
CREATE TRIGGER guard_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON guards
    FOR EACH ROW
    EXECUTE PROCEDURE guard_audit_function();
"""
