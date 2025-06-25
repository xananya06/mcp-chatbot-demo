"""change pricing to text

Revision ID: e63cc2b7a066
Revises: complete_001
Create Date: 2024-06-24 13:33:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e63cc2b7a066'
down_revision = 'complete_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change pricing column from String to Text
    op.alter_column('discovered_tools', 'pricing',
                    existing_type=sa.String(),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert pricing column from Text to String
    op.alter_column('discovered_tools', 'pricing',
                    existing_type=sa.Text(),
                    type_=sa.String(),
                    existing_nullable=True)