from typing import Any

from sqlalchemy import text
from starlite import Starlite, get

from src.core.db import AsyncScopedSession
from src.core.middlewares import TimeoutMiddleware, TimingMiddleware
from src.settings import log_config, openapi_config


@get("/")
def index() -> str:
    """Index function that retuns a "Hello World"."""
    return "Hello World"


@get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check handler."""
    assert (await AsyncScopedSession().execute(text("SELECT 1"))).scalar_one() == 1
    return {"app": "Shinji"}


app = Starlite(
    route_handlers=[index, health_check],
    openapi_config=openapi_config,
    logging_config=log_config,
    middleware=[TimeoutMiddleware, TimingMiddleware],
)
