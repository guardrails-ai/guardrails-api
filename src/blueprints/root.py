from flask import Blueprint
from sqlalchemy import text
from src.classes.health_check import HealthCheck
from src.clients.postgres_client import PostgresClient
from src.utils.handle_error import handle_error
from src.utils.gather_request_metrics import gather_request_metrics
from src.utils.logger import logger

root_bp = Blueprint("root", __name__, url_prefix="/")


@root_bp.route("/")
@handle_error
@gather_request_metrics
def home():
    return "Hello, Flask!"


@root_bp.route("/health-check")
@handle_error
@gather_request_metrics
def health_check():
    # Make sure we're connected to the database and can run queries
    pg_client = PostgresClient()
    query = text("SELECT count(datid) FROM pg_stat_activity;")
    response = pg_client.db.session.execute(query).all()
    logger.info("response: ", response)
    # There's probably a better way to serialize these classes built into Flask
    return HealthCheck(200, "Ok").to_dict()
