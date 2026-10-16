"""add_password_hash_and_user_sessions

Revision ID: 8b08f98031ea
Revises: a62c769b5f6c
Create Date: 2026-10-16 11:01:19.988280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8b08f98031ea'
down_revision: Union[str, Sequence[str], None] = 'a62c769b5f6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_sessions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True, precision=3), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True, precision=3), nullable=False),
    sa.Column('revoked_at', postgresql.TIMESTAMP(timezone=True, precision=3), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_token_hash'), 'user_sessions', ['token_hash'], unique=True)
    op.add_column('users', sa.Column('password_hash', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password_hash')
    op.drop_index(op.f('ix_user_sessions_token_hash'), table_name='user_sessions')
    op.drop_table('user_sessions')
