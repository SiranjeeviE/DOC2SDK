import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

def normalize_database_url(url: str) -> str:
    """
    Normalizes database URLs, replacing legacy postgres:// with postgresql+psycopg2://
    for explicit SQLAlchemy driver compatibility.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

DATABASE_URL = normalize_database_url(
    os.environ.get("DATABASE_URL", "sqlite:///./antigravity.db")
)

is_production = (
    os.environ.get("ENVIRONMENT", "").lower() in ("production", "prod")
    or bool(os.environ.get("RENDER"))
)

def create_db_engine(url: str = DATABASE_URL):
    normalized_url = normalize_database_url(url)
    
    if "sqlite" in normalized_url:
        if is_production:
            logger.warning(
                "WARNING: SQLite configured in production environment. "
                "PostgreSQL should be used for concurrent production workloads."
            )
        eng = create_engine(
            normalized_url,
            connect_args={"check_same_thread": False},
        )
        # Enforce foreign key constraints in SQLite
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return eng

    # Production PostgreSQL connection pool configuration
    pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
    max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.environ.get("DB_POOL_RECYCLE", "300"))
    
    return create_engine(
        normalized_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=pool_recycle,
    )

engine = create_db_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Creates database tables for local development/testing if not managed by migrations.
    """
    from ..models.base import Base
    from ..models import domain  # noqa
    Base.metadata.create_all(bind=engine)
