from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.exception_handlers import (
    handle_app_error,
    handle_unexpected_error,
    handle_validation_error,
)
from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logger import setup_logging


def create_app() -> FastAPI:

    setup_logging()

    app = FastAPI(
        title=settings.app_name,
        description="REST API for The Orc Shack restaurant",
        version="1.0.0",
    )

    # Register global custom exception handler
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_unexpected_error)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(health_router)

    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
