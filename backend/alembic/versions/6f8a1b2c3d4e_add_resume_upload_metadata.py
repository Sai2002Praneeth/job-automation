'''add resume upload metadata

Revision ID: 6f8a1b2c3d4e
Revises: 3d6ac7b8e9f0
Create Date: 2026-07-06 00:00:00.000000

'''
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6f8a1b2c3d4e'
down_revision: Union[str, Sequence[str], None] = '3d6ac7b8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    '''Add metadata captured when a resume is uploaded.'''
    op.add_column(
        'resumes',
        sa.Column(
            'filename',
            sa.String(length=255),
            nullable=False,
            server_default='',
        ),
    )
    op.add_column(
        'resumes',
        sa.Column(
            'content_type',
            sa.String(length=255),
            nullable=False,
            server_default='application/pdf',
        ),
    )
    op.add_column(
        'resumes',
        sa.Column(
            'file_size',
            sa.BigInteger(),
            nullable=False,
            server_default='0',
        ),
    )
    op.alter_column('resumes', 'filename', server_default=None)
    op.alter_column('resumes', 'content_type', server_default=None)
    op.alter_column('resumes', 'file_size', server_default=None)


def downgrade() -> None:
    '''Remove resume upload metadata.'''
    op.drop_column('resumes', 'file_size')
    op.drop_column('resumes', 'content_type')
    op.drop_column('resumes', 'filename')
