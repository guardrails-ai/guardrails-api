import os
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_seasurf import SeaSurf
# from flask_talisman import Talisman


def create_app():
    app = Flask(__name__)
    CORS(app)
    
    host = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
    if host.startswith("https://"):
        SeaSurf(app)
        # Talisman(app, force_https_permanent=True)
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
