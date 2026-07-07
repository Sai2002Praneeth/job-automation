"""add resume projects

Revision ID: 3d6ac7b8e9f0
Revises: 9c587f027893
Create Date: 2026-07-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3d6ac7b8e9f0"
down_revision: Union[str, Sequence[str], None] = "9c587f027893"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "resumes",
        sa.Column(
            "projects",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.alter_column("resumes", "projects", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("resumes", "projects")
