from flask import Flask
from swagger_ui import api_doc

app = Flask(__name__)


def create_app():
    app = Flask(__name__)
    api_doc(
        app,
        config_path="./open-api-spec.yml",
        url_prefix="/docs",
        title="GuardRails API Docs",
    )

    from src.clients.postgres_client import PostgresClient

    pg_client = PostgresClient()
    pg_client.initialize(app)

    from src.blueprints.root import root_bp
    from src.blueprints.guards import guards_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(guards_bp)

    return app
