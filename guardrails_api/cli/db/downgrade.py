import os
from typing import Annotated
import typer
from dotenv import load_dotenv
from guardrails_api.cli.db.db import db_command
from guardrails_api.db.migrations.downgrade import downgrade as downgrade_db


@db_command.command(name="downgrade")
def downgrade(
    revision: Annotated[str, typer.Argument()] = "-1",
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

    downgrade_db(revision)
