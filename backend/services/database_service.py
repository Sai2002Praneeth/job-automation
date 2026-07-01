from sqlalchemy import text
from sqlalchemy.orm import Session


def is_database_reachable(database_session: Session) -> bool:
    """Return whether the configured database responds to a simple query."""
    return database_session.scalar(text("SELECT 1")) == 1
