import os

from alembic import command
from alembic.config import Config

from guardrails_api.db.get_db_url import get_db_url


def upgrade(revision: str = "head"):
    migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    alembic_cfg = Config()

    alembic_cfg.set_main_option("script_location", migrations_dir)

    database_url = get_db_url()
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    print(f"Running Alembic upgrade to '{revision}'...")
    command.upgrade(alembic_cfg, revision)
    print("Alembic upgrade complete.")
