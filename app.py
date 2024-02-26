import os
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    host = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
    if host.startswith("https://"):
        from flask_talisman import Talisman
        Talisman(app)
    
    CORS(app)

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
