"""A module containing endpoints for the application health check"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.database import check_database_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> JSONResponse:
    if not check_database_connection():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy"},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"},
    )
