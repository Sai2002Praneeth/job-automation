from sqlalchemy import Engine, create_engine

from config import settings


engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
