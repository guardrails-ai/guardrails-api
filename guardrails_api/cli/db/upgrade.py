import os
from typing import Annotated
import typer
from dotenv import load_dotenv
from guardrails_api.cli.db.db import db_command
from guardrails_api.db.migrations.upgrade import upgrade as upgrade_db


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

    upgrade_db(revision)
