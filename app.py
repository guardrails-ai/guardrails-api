import os
from flask import Flask, request, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        self_endpoint = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
        print("SELF_ENDPOINT is ", self_endpoint)
        url = urlparse(self_endpoint)
        print("setting environ['wsgi.url_scheme'] to ", url.scheme)
        environ['wsgi.url_scheme'] = url.scheme
        return self.app(environ, start_response)


def create_app():
    app = Flask(__name__)

    @app.before_request
    def trace_requests_before():
        print(f"Request {request.endpoint or request.url or request.path} received!")

    @app.after_request
    def trace_requests_after(response: Response):
        print(f"Responding to request with status: {response.status}")
        return response

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

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
