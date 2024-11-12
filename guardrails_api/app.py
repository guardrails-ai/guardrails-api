import os
from typing import Optional
from flask import Flask, Response, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse
from guardrails import configure_logging
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from guardrails_api.clients.postgres_client import postgres_is_enabled
from guardrails_api.otel import otel_is_disabled, initialize
from guardrails_api.utils.trace_server_start_if_enabled import (
    trace_server_start_if_enabled,
)
from guardrails_api.clients.cache_client import CacheClient
from rich.console import Console
from rich.rule import Rule


# TODO: Move this to a separate file
class OverrideJsonProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if callable(o):
            return str(o)
        return super().default(o)


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        self_endpoint = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
        url = urlparse(self_endpoint)
        environ["wsgi.url_scheme"] = url.scheme
        return self.app(environ, start_response)


def register_config(config: Optional[str] = None):
    default_config_file = os.path.join(os.getcwd(), "./config.py")
    config_file = config or default_config_file
    config_file_path = os.path.abspath(config_file)
    if os.path.isfile(config_file_path):
        from importlib.machinery import SourceFileLoader

        # This creates a module named "validators" with the contents of the init file
        # This allow statements like `from validators import StartsWith`
        # But more importantly, it registers all of the validators imported in the init
        SourceFileLoader("config", config_file_path).load_module()


def create_app(
    env: Optional[str] = None, config: Optional[str] = None, port: Optional[int] = None
):
    trace_server_start_if_enabled()
    # used to print user-facing messages during server startup
    console = Console()

    if os.environ.get("APP_ENVIRONMENT") != "production":
        from dotenv import load_dotenv

        # Always load default env file, but let user specified file override it.
        default_env_file = os.path.join(os.path.dirname(__file__), "default.env")
        load_dotenv(default_env_file, override=True)

        if env:
            env_file_path = os.path.abspath(env)
            load_dotenv(env_file_path, override=True)

    set_port = port or os.environ.get("PORT", 8000)
    host = os.environ.get("HOST", "http://localhost")
    self_endpoint = os.environ.get("SELF_ENDPOINT", f"{host}:{set_port}")
    os.environ["SELF_ENDPOINT"] = self_endpoint

    register_config(config)

    app = Flask(__name__)
    app.json = OverrideJsonProvider(app)

    app.config["APPLICATION_ROOT"] = "/"
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    CORS(app)

    @app.before_request
    def basic_cors():
        if request.method.lower() == "options":
            return Response()

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    guardrails_log_level = os.environ.get("GUARDRAILS_LOG_LEVEL", "INFO")
    configure_logging(log_level=guardrails_log_level)

    if not otel_is_disabled():
        FlaskInstrumentor().instrument_app(app)
        initialize()

    # if no pg_host is set, don't set up postgres
    if postgres_is_enabled():
        from guardrails_api.clients.postgres_client import PostgresClient

        pg_client = PostgresClient()
        pg_client.initialize(app)

    cache_client = CacheClient()
    cache_client.initialize(app)

    from guardrails_api.blueprints.root import root_bp
    from guardrails_api.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    console.print(f"\n:rocket: Guardrails API is available at {self_endpoint}")
    console.print(
        f":book: Visit {self_endpoint}/docs to see available API endpoints.\n"
    )

    console.print(":green_circle: Active guards and OpenAI compatible endpoints:")

    with app.app_context():
        from guardrails_api.blueprints.guards import guard_client

        for g in guard_client.get_guards():
            g = g.to_dict()
            console.print(
                f"- Guard: [bold white]{g.get('name')}[/bold white] {self_endpoint}/guards/{g.get('name')}/openai/v1"
            )

    console.print("")
    console.print(
        Rule("[bold grey]Server Logs[/bold grey]", characters="=", style="white")
    )

    return app
