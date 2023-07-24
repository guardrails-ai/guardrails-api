from flask import Blueprint
from sqlalchemy import text
from src.classes import HealthCheck
from src.clients import PostgresClient
from src.utils import handle_error, logger

root_bp = Blueprint("root", __name__, url_prefix="/")


@root_bp.route("/")
@handle_error
def home():
    return "Hello, Flask!"


@root_bp.route("/health-check")
@handle_error
def health_check():
    # Make sure we're connected to the database and can run queries
    pg_client = PostgresClient()
    query = text("SELECT count(datid) FROM pg_stat_activity;")
    response = pg_client.db.session.execute(query).all()
    logger.info("response: ", response)
    # There's probably a better way to serialize these classes built into Flask
    return HealthCheck(200, "Ok").to_dict()
