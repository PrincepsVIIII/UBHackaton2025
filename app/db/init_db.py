"""
Utility for initializing the database schema.
"""

from __future__ import annotations

from app.db.session import Base, engine
from app import models  # noqa: F401  Import models to ensure they are registered with SQLAlchemy


def init_db() -> None:
    """
    Create all database tables. Run this when setting up a new environment.
    """

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()

