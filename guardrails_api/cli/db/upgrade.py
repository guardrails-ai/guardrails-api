import os
from typing import Annotated
import typer
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv
from guardrails_api.cli.db.db import db_command
from guardrails_api.db.get_db_url import get_db_url


@db_command.command(name="upgrade")
def upgrade(
    revision: Annotated[str, typer.Argument()] = "head",
    env: str = typer.Option(
        default=".env",
        help="An env file to load environment variables from.",
    ),
    env_override: bool = typer.Option(
        default=False,
        help="Override existing environment variables with values from the env file.",
    ),
):
    env_file_path = os.path.abspath(env)
    if os.path.isfile(env_file_path):
        load_dotenv(env_file_path, override=env_override)

    migrations_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "db", "migrations")
    )

    alembic_cfg = Config()

    alembic_cfg.set_main_option("script_location", migrations_dir)

    database_url = get_db_url()
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    print(f"Running Alembic upgrade to '{revision}'...")
    command.upgrade(alembic_cfg, revision)
    print("Alembic upgrade complete.")
