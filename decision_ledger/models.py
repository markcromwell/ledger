"""SQLAlchemy ORM models for the Decision Ledger."""
from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Integer, String, Text, func

from decision_ledger.database import Base

DECISION_STATUSES = ("proposed", "adopted", "superseded", "rejected")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    context = Column(Text, nullable=True)
    decision = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="proposed", server_default="proposed")
    decided_on = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )