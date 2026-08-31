"""
Database setup.

Using SQLite for now since it's zero-config and this is a single-instance
dispatch server. If you later run multiple backend replicas behind a load
balancer, swap DATABASE_URL for Postgres — the models/queries don't change,
only the ConnectionManager (see connection_manager.py) would need Redis
pub/sub instead of the in-memory dict, since WebSocket connections would be
split across replicas.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dispatch.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models here so they're registered on Base before create_all
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)