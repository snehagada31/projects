"""add_is_active_to_users

Revision ID: 089a1f8a60c3
Revises: 8b08f98031ea
Create Date: 2026-10-16 12:15:05.437906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '089a1f8a60c3'
down_revision: Union[str, Sequence[str], None] = '8b08f98031ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_active')

