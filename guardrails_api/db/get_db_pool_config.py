from typing import TypedDict

from guardrails_api.utils.get_int_env_var import get_int_env_var


class PgPoolConfig(TypedDict):
    pool_size: int | None
    max_overflow: int | None
    pool_timeout: int | None


def get_db_pool_config() -> PgPoolConfig:
    pool_size = get_int_env_var("PG_POOL_SIZE")
    max_overflow = get_int_env_var("PG_POOL_MAX_OVERFLOW")
    pool_timeout = get_int_env_var("PG_POOL_TIMEOUT")

    return {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
    }
