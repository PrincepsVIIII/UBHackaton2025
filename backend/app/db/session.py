"""
Database session and engine configuration.

This module sets up the SQLAlchemy engine and session factory using an SQLite
database stored at the project root (app.db). Declarative Base is provided for
future ORM models.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a SQLAlchemy session.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

