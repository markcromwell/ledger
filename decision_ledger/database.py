"""SQLAlchemy engine, session factory, and declarative base."""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Name the driver explicitly. A bare "postgresql://" URL lets SQLAlchemy pick a
# default DBAPI that may not be installed; pinning "+psycopg2" (with psycopg2-binary
# in requirements) means prod startup fails loudly at install time, not at runtime.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://localhost:5432/decision_ledger",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()