from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.session import get_db
from services.database_service import is_database_reachable


router = APIRouter(prefix="/health", tags=["health"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/database")
def database_health_check(database_session: DatabaseSession) -> dict[str, str]:
    try:
        if is_database_reachable(database_session):
            return {"status": "healthy", "database": "reachable"}
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unreachable.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database health check failed.",
    )
