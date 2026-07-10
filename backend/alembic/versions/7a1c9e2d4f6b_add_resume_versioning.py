"""add resume versioning

Revision ID: 7a1c9e2d4f6b
Revises: 6f8a1b2c3d4e
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a1c9e2d4f6b"
down_revision: Union[str, Sequence[str], None] = "6f8a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add version metadata to resumes."""
    op.add_column(
        "resumes",
        sa.Column("root_resume_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.execute(
        """
        UPDATE resumes
        SET root_resume_id = roots.root_resume_id
        FROM (SELECT MIN(id) AS root_resume_id FROM resumes) AS roots
        WHERE roots.root_resume_id IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE resumes
        SET version_number = ordered.version_number
        FROM (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS version_number
            FROM resumes
        ) AS ordered
        WHERE resumes.id = ordered.id
        """
    )
    op.execute(
        """
        UPDATE resumes
        SET is_active = (id = (SELECT MAX(id) FROM resumes))
        """
    )

    op.alter_column("resumes", "version_number", server_default=None)
    op.alter_column("resumes", "is_active", server_default=None)
    op.create_index(
        "ix_resumes_root_resume_id",
        "resumes",
        ["root_resume_id"],
    )
    op.create_foreign_key(
        "fk_resumes_root_resume_id_resumes",
        "resumes",
        "resumes",
        ["root_resume_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove version metadata from resumes."""
    op.drop_constraint(
        "fk_resumes_root_resume_id_resumes",
        "resumes",
        type_="foreignkey",
    )
    op.drop_index("ix_resumes_root_resume_id", table_name="resumes")
    op.drop_column("resumes", "is_active")
    op.drop_column("resumes", "version_number")
    op.drop_column("resumes", "root_resume_id")
