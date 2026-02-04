"""
Database session management for Noon-E-Commerce
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Database URL from environment
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://aidev:AiDev_Secure_2024!@172.19.0.3:5432/aidev'
)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Use with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use in non-FastAPI code.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
