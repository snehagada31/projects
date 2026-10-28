"""create notification preferences table

Revision ID: a1b2c3d4e5f6
Revises: f1e2d3c4b5a6
Create Date: 2026-10-27 02:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_notification_preferences',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('likes', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('reposts', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('replies', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('follows', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('user_notification_preferences')
