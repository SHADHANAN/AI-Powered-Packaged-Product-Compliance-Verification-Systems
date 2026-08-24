"""initial baseline schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline initial migration upgrade (Phase 2 foundation)."""
    pass


def downgrade() -> None:
    """Baseline initial migration downgrade."""
    pass
