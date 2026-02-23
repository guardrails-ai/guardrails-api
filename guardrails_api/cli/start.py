import os
from dotenv import load_dotenv
import typer
from guardrails_api.cli.cli import cli
from guardrails_api.app import create_app
from guardrails_api.utils.configuration import valid_configuration
import uvicorn


@cli.command("start")
def start(
    env: str = typer.Option(
        default=".env",
        help="An env file to load environment variables from.",
    ),
    config: str = typer.Option(
        default="",
        help="A config file to load Guards from.",
    ),
    port: int = typer.Option(
        default=8000,
        help="The port to run the server on.",
    ),
    env_override: bool = typer.Option(
        default=True,
        help="Override existing environment variables with values from the env file.",
    ),
):
    env_file_path = os.path.abspath(env)
    if os.path.isfile(env_file_path):
        load_dotenv(env_file_path, override=env_override)

    valid_configuration(config)

    port = port or 8000

    app = create_app(env, config, port)
    uvicorn.run(app, port=port, env_file=env_file_path)
