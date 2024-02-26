import os
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse
from flask_talisman import Talisman


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    self_endpoint = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
    url = urlparse(self_endpoint)
    alt_scheme = 'https'
    if url.scheme == 'https':
        alt_scheme = 'http'
    
    alt_endpoint = f"{alt_scheme}://{url.hostname}"
    Talisman(
        app,
        force_https=False,
        content_security_policy={
            "default-src": [
                "'self'",
                self_endpoint,
                alt_endpoint,
                "https://unpkg.com",
                "http://www.w3.org"
            ],
            "script-src": [
                "'self'",
                self_endpoint,
                alt_endpoint,
                "https://unpkg.com",
                "http://www.w3.org"
            ],
            "img-src": [
                "'self'",
                "data:",
                self_endpoint,
                alt_endpoint,
                "https://unpkg.com",
                "http://www.w3.org"
            ]
        },
        content_security_policy_nonce_in=["script-src"]
    )
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
        x_prefix=1
    )
    
    

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
