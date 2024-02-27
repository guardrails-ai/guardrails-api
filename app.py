import os
from flask import Flask, request, Response
from flask_cors import CORS
# from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse
# from flask_talisman import Talisman


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
    
    @app.before_request
    def trace_requests_before():
        print(f"Request {request.endpoint or request.url or request.path} received!")

    @app.after_request
    def trace_requests_after(response: Response):
        print(f"Responding to request with status: {response.status}")
        return response
    
    app.config["PREFERRED_URL_SCHEME"] = "https"
    ReverseProxied(app)
    CORS(app)

    # alt_scheme = 'https'
    # alt_port = 80
    # if url.scheme == 'https':
    #     alt_scheme = 'http'
    #     alt_port = 443

    # alt_endpoint = f"{alt_scheme}://{url.hostname}"
    # alt_endpoint_w_port = f"{alt_scheme}://{url.hostname}:{alt_port}"
    # Talisman(
    #     app,
    #     force_https=False,
    #     content_security_policy={
    #         "default-src": [
    #             "'self'",
    #             self_endpoint,
    #             alt_endpoint,
    #             alt_endpoint_w_port,
    #             "https://unpkg.com",
    #             "http://www.w3.org"
    #         ],
    #         "script-src": [
    #             "'self'",
    #             self_endpoint,
    #             alt_endpoint,
    #             alt_endpoint_w_port,
    #             "https://unpkg.com",
    #             "http://www.w3.org"
    #         ],
    #         "img-src": [
    #             "'self'",
    #             "data:",
    #             self_endpoint,
    #             alt_endpoint,
    #             alt_endpoint_w_port,
    #             "https://unpkg.com",
    #             "http://www.w3.org"
    #         ]
    #     },
    #     content_security_policy_nonce_in=["script-src"]
    # )
    # app.wsgi_app = ProxyFix(
    #     app.wsgi_app,
    #     x_for=0,
    #     x_proto=0,
    #     # x_host=1,
    #     # x_port=1,
    #     # x_prefix=1
    # )

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
