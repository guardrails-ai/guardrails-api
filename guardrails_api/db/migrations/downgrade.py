import os

from alembic import command
from alembic.config import Config

from guardrails_api.db.get_db_url import get_db_url


def downgrade(revision: str = "-1"):
    migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    alembic_cfg = Config()

    alembic_cfg.set_main_option("script_location", migrations_dir)

    database_url = get_db_url()
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    print(f"Running Alembic downgrade to '{revision}'...")
    command.downgrade(alembic_cfg, revision)
    print("Alembic downgrade complete.")
