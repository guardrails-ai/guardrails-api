import os
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse
from guardrails import configure_logging
# from opentelemetry.instrumentation.flask import FlaskInstrumentor


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        self_endpoint = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
        url = urlparse(self_endpoint)
        environ['wsgi.url_scheme'] = url.scheme
        return self.app(environ, start_response)


def create_app():
    app = Flask(__name__)

    app.config['APPLICATION_ROOT'] = '/'
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    CORS(app)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1
    )

    guardrails_log_level = os.environ.get("GUARDRAILS_LOG_LEVEL", "INFO")
    configure_logging(log_level=guardrails_log_level)

    # FlaskInstrumentor().instrument_app(app)

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
