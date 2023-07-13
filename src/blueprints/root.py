from flask import Blueprint
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.clients.postgres_client import PostgresClient
from src.utils.handle_error import handle_error

rootBp = Blueprint("root", __name__, url_prefix="/")


@rootBp.route("/")
@handle_error
def home():
    return "Hello, Flask!"


@rootBp.route("/health-check")
@handle_error
def healthCheck():
    # Make sure we're connected to the database and can run queries
    pgClient = PostgresClient()
    query = text("SELECT count(datid) FROM pg_stat_activity;")
    response = pgClient.db.session.execute(query).all()
    print("response: ", response)
    # There's probably a better way to serialize these classes built into Flask
    return HealthCheck(200, "Ok").to_dict()
