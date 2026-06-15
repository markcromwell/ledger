"""Pydantic schemas for Decision Ledger API requests and responses."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DecisionStatus(str, Enum):
    proposed = "proposed"
    adopted = "adopted"
    superseded = "superseded"
    rejected = "rejected"


class DecisionCreate(BaseModel):
    title: str
    context: Optional[str] = None
    decision: Optional[str] = None
    status: DecisionStatus = DecisionStatus.proposed
    decided_on: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("title must not be empty")
        return value.strip()


class DecisionPatch(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None
    decision: Optional[str] = None
    status: Optional[DecisionStatus] = None
    decided_on: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("title must not be empty")
        return value.strip() if value is not None else None


class DecisionRead(BaseModel):
    id: int
    title: str
    context: Optional[str] = None
    decision: Optional[str] = None
    status: DecisionStatus
    decided_on: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}