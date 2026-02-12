import os
from dotenv import load_dotenv
import typer
from typing import Optional
from guardrails_api.cli.cli import cli
from guardrails_api.app import create_app
from guardrails_api.utils.configuration import valid_configuration
import uvicorn


@cli.command("start")
def start(
    env: Optional[str] = typer.Option(
        default="",
        help="An env file to load environment variables from.",
    ),
    config: Optional[str] = typer.Option(
        default="",
        help="A config file to load Guards from.",
    ),
    port: Optional[int] = typer.Option(
        default=8000,
        help="The port to run the server on.",
    ),
):
    env = env or None
    env_file_path = None
    if env:
        env_file_path = os.path.abspath(env)
        load_dotenv(env_file_path, override=True)

    config = config or None
    valid_configuration(config)

    port = port or 8000

    app = create_app(env, config, port)
    uvicorn.run(app, port=port, env_file=env_file_path)
