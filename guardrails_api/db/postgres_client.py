import os
import threading
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from guardrails_api.db.get_db_pool_config import get_db_pool_config
from guardrails_api.db.get_db_url import get_db_url
from guardrails_api.db.migrations.upgrade import upgrade
from guardrails_api.db.models.base import Base


def postgres_is_enabled() -> bool:
    return (
        os.environ.get("PGHOST", None) or os.environ.get("DB_URL", None)
    ) is not None


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
        print("\n==> PostgresClient.initialize was called")
        url = get_db_url()
        pool_config = get_db_pool_config()
        pool_config_kwargs = {k: v for k, v in pool_config.items() if v is not None}

        # TODO: Make this a default and allow users to pass in their own SQL Alchemy engine
        engine = create_engine(url, **pool_config_kwargs)
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
                self.run_initialization()
                # Release the lock after initialization is complete
                connection.execute(text(f"SELECT pg_advisory_unlock({lock_id});"))

    def run_initialization(self):
        # Perform the actual initialization tasks
        from guardrails_api.db.models import GuardItem, GuardItemAudit  # noqa

        Base.metadata.create_all(bind=self.engine)

        # Migrate to latest schema
        upgrade()
