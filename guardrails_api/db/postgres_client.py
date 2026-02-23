import os
import threading
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from guardrails_api.db.get_db_url import get_db_url
from guardrails_api.db.models.base import Base


def postgres_is_enabled() -> bool:
    return os.environ.get("PGHOST", None) is not None


# Global variables for database session
postgres_client = None
SessionLocal = None


class PostgresClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                cls._instance = super(PostgresClient, cls).__new__(cls)
        return cls._instance

    def get_db(self):
        if postgres_is_enabled():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()
        else:
            yield None

    def generate_lock_id(self, name: str) -> int:
        import hashlib

        return int(hashlib.sha256(name.encode()).hexdigest(), 16) % (2**63)

    def initialize(self, app: FastAPI):
        conf = get_db_url()
        engine = create_engine(conf)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        self.app = app
        self.engine = engine
        self.SessionLocal = SessionLocal

        lock_id = self.generate_lock_id("guardrails-api")

        # Use advisory lock to ensure only one worker runs initialization
        with engine.begin() as connection:
            lock_acquired = connection.execute(
                text(f"SELECT pg_try_advisory_lock({lock_id});")
            ).scalar()
            if lock_acquired:
                self.run_initialization(connection)
                # Release the lock after initialization is complete
                connection.execute(text(f"SELECT pg_advisory_unlock({lock_id});"))

    def run_initialization(self, connection):
        # Perform the actual initialization tasks
        from guardrails_api.db.models import GuardItem, GuardItemAudit  # noqa

        Base.metadata.create_all(bind=self.engine)

        # Execute custom SQL extensions and triggers
        connection.execute(text(AUDIT_FUNCTION))
        connection.execute(text(AUDIT_TRIGGER))


AUDIT_FUNCTION = """
CREATE OR REPLACE FUNCTION guard_audit_function() RETURNS TRIGGER AS $guard_audit$
BEGIN
    IF (TG_OP = 'DELETE') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), OLD.*, now(), 'D';
    ELSIF (TG_OP = 'UPDATE') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), OLD.*, now(), 'U';
    ELSIF (TG_OP = 'INSERT') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), NEW.*, now(), 'I';
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
