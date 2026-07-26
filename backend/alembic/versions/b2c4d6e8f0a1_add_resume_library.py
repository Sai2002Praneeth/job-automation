"""add resume library

Revision ID: b2c4d6e8f0a1
Revises: 7a1c9e2d4f6b
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, Sequence[str], None] = "7a1c9e2d4f6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create named resume libraries and attach versions to them."""
    op.create_table(
        "resume_libraries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_libraries_name",
        "resume_libraries",
        ["name"],
        unique=True,
    )

    op.add_column(
        "resumes",
        sa.Column("resume_library_id", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        WITH legacy_histories AS (
            SELECT
                COALESCE(root_resume_id, id) AS legacy_root_id,
                MIN(NULLIF(filename, '')) AS filename
            FROM resumes
            GROUP BY COALESCE(root_resume_id, id)
        )
        INSERT INTO resume_libraries (name)
        SELECT
            LEFT(
                COALESCE(filename, 'Resume') || ' ' || legacy_root_id::text,
                255
            )
        FROM legacy_histories
        ORDER BY legacy_root_id
        """
    )

    op.execute(
        """
        WITH legacy_histories AS (
            SELECT
                COALESCE(root_resume_id, id) AS legacy_root_id,
                LEFT(
                    COALESCE(MIN(NULLIF(filename, '')), 'Resume')
                    || ' ' || COALESCE(root_resume_id, id)::text,
                    255
                ) AS library_name
            FROM resumes
            GROUP BY COALESCE(root_resume_id, id)
        )
        UPDATE resumes
        SET resume_library_id = resume_libraries.id
        FROM legacy_histories
        JOIN resume_libraries
            ON resume_libraries.name = legacy_histories.library_name
        WHERE COALESCE(resumes.root_resume_id, resumes.id)
            = legacy_histories.legacy_root_id
        """
    )

    op.execute(
        """
        UPDATE resumes
        SET is_active = (resumes.id = active_versions.id)
        FROM (
            SELECT DISTINCT ON (resume_library_id)
                id,
                resume_library_id
            FROM resumes
            ORDER BY
                resume_library_id,
                is_active DESC,
                version_number DESC,
                id DESC
        ) AS active_versions
        WHERE resumes.resume_library_id = active_versions.resume_library_id
        """
    )

    op.alter_column(
        "resumes",
        "resume_library_id",
        nullable=False,
    )
    op.create_index(
        "ix_resumes_resume_library_id",
        "resumes",
        ["resume_library_id"],
    )
    op.create_foreign_key(
        "fk_resumes_resume_library_id_resume_libraries",
        "resumes",
        "resume_libraries",
        ["resume_library_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_resumes_library_version_number",
        "resumes",
        ["resume_library_id", "version_number"],
    )
    op.create_index(
        "uq_resumes_one_active_per_library",
        "resumes",
        ["resume_library_id"],
        unique=True,
        postgresql_where=sa.text("is_active IS TRUE"),
    )


def downgrade() -> None:
    """Remove named resume libraries."""
    op.drop_index(
        "uq_resumes_one_active_per_library",
        table_name="resumes",
        postgresql_where=sa.text("is_active IS TRUE"),
    )
    op.drop_constraint(
        "uq_resumes_library_version_number",
        "resumes",
        type_="unique",
    )
    op.drop_constraint(
        "fk_resumes_resume_library_id_resume_libraries",
        "resumes",
        type_="foreignkey",
    )
    op.drop_index("ix_resumes_resume_library_id", table_name="resumes")
    op.drop_column("resumes", "resume_library_id")
    op.drop_index("ix_resume_libraries_name", table_name="resume_libraries")
    op.drop_table("resume_libraries")
