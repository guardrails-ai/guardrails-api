import typer
from typing import Optional
from gunicorn.app.base import BaseApplication
from guardrails_api.cli.cli import cli
from guardrails_api.app import create_app


class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


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
    timeout: Optional[int] = typer.Option(
        default=5,
        help="Gunicorn worker timeout.",
    ),
    threads: Optional[int] = typer.Option(
        default=10,
        help="Number of Gunicorn worker threads.",
    ),
    port: Optional[int] = typer.Option(
        default=8000,
        help="The port to run the server on.",
    ),
):
    # TODO: If these are empty,
    #   look for them in a .guardrailsrc in the current directory.
    env = env or None
    config = config or None

    options = {
        "bind": f"0.0.0.0:{port}",
        "timeout": timeout,
        "threads": threads,
    }
    StandaloneApplication(create_app(env, config, port), options).run()
