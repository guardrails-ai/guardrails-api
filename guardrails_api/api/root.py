from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from sqlalchemy import text
from guardrails_api.classes.health_check import HealthCheck
from guardrails_api.db.postgres_client import PostgresClient, postgres_is_enabled
from guardrails_api.utils.logger import logger


class HealthCheckResponse(BaseModel):
    status: int
    message: str


router = APIRouter()


@router.get("/")
async def home():
    return "Hello, world!"


@router.get("/health-check", response_model=HealthCheckResponse)
async def health_check():
    try:
        if not postgres_is_enabled():
            return HealthCheck(200, "Ok").to_dict()

        pg_client = PostgresClient()
        query = text("SELECT count(datid) FROM pg_stat_activity;")
        with pg_client.SessionLocal() as session:
            response = session.execute(query).all()

            logger.debug("response: %s", response)

            return HealthCheck(200, "Ok").to_dict()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
