from flask import Flask

from src.classes.health_check import HealthCheck
from src.classes.http_error import HttpError
from flask_sqlalchemy import SQLAlchemy
from src.classes.validation_output import ValidationOutput
from swagger_ui import api_doc

from src.clients.postgres_client import PostgresClient

from src.clients.guard_client import GuardClient
app = Flask(__name__)

def create_app():
    app = Flask(__name__)
    api_doc(app, config_path='./open-api-spec.yml', url_prefix='/docs', title='GuardRails API Docs')

    from src.clients.postgres_client import PostgresClient
    pgClient = PostgresClient()
    pgClient.initialize(app)

    from src.blueprints.root import rootBp
    from src.blueprints.guards import guardsBp
    app.register_blueprint(rootBp)
    app.register_blueprint(guardsBp)
    
    return app