"""create decisions table

Revision ID: 3371
Revises:
Create Date: 2026-06-15

"""
from typing import Sequence, Union

from alembic import op

revision: str = "3371"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            context TEXT,
            decision TEXT,
            status VARCHAR NOT NULL DEFAULT 'proposed',
            decided_on DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decisions")