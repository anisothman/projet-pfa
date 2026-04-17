"""FastAPI app factory. Wires middleware, logging, routers, and startup checks."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from localis import __version__
from localis.api.routes import analyze, candidates, health, report
from localis.core.config import get_settings
from localis.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)
    settings.check_keys()
    logger = get_logger("localis")
    logger.info("localis.startup", version=__version__, primary=settings.llm_primary)
    yield
    logger.info("localis.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Localis AI",
        version=__version__,
        description="Business intelligence reports powered by Google + LLMs.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(candidates.router)
    app.include_router(analyze.router)
    app.include_router(report.router)
    return app


app = create_app()
