"""Add discovered tools table

Revision ID: 2a2c065e61a2
Revises: 1a1c065e61a1
Create Date: 2025-06-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2a2c065e61a2'
down_revision = '1a1c065e61a1'  # Points directly to your initial migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discovered_tools table
    op.create_table('discovered_tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tool_type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('pricing', sa.String(), nullable=True),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovered_tools_id'), 'discovered_tools', ['id'], unique=False)
    op.create_index(op.f('ix_discovered_tools_name'), 'discovered_tools', ['name'], unique=False)
    op.create_index(op.f('ix_discovered_tools_tool_type'), 'discovered_tools', ['tool_type'], unique=False)


def downgrade() -> None:
    # Drop discovered_tools table
    op.drop_index(op.f('ix_discovered_tools_tool_type'), table_name='discovered_tools')
    op.drop_index(op.f('ix_discovered_tools_name'), table_name='discovered_tools')
    op.drop_index(op.f('ix_discovered_tools_id'), table_name='discovered_tools')
    op.drop_table('discovered_tools')