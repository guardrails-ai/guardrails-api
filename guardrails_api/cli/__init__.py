import importlib
import typer
import guardrails_api.cli.start  # noqa
from typing import Optional
from guardrails_api.cli.cli import cli
from guardrails_api.cli.db import db_command

cli.add_typer(db_command, name="db", help="Manage database migrations.")


def version_callback(value: bool):
    if value:
        version = importlib.metadata.version("guardrails-api")
        print(f"guardrails-api CLI Version: {version}")
        raise typer.Exit()


@cli.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    pass


if __name__ == "__main__":
    cli()
