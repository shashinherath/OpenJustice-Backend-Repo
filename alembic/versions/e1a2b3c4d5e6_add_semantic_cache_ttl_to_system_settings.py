"""add_semantic_cache_ttl_to_system_settings

Revision ID: e1a2b3c4d5e6
Revises: 9906f84aea5f
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, None] = '9906f84aea5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'system_settings',
        sa.Column('semantic_cache_ttl_hours', sa.Integer(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('system_settings', 'semantic_cache_ttl_hours')
