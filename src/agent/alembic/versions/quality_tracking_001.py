"""Add quality tracking fields to discovered_tools table

Revision ID: quality_tracking_001
Revises: e63cc2b7a066
Create Date: 2025-07-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'quality_tracking_001'
down_revision = 'e63cc2b7a066'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add quality tracking fields to discovered_tools table
    op.add_column('discovered_tools', sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True))
    op.add_column('discovered_tools', sa.Column('website_status', sa.Integer(), nullable=True))
    op.add_column('discovered_tools', sa.Column('user_reports', sa.Integer(), nullable=True))
    op.execute("UPDATE discovered_tools SET user_reports = 0 WHERE user_reports IS NULL")
    op.alter_column('discovered_tools', 'user_reports', nullable=False)
    op.add_column('discovered_tools', sa.Column('canonical_url', sa.String(), nullable=True))
    op.add_column('discovered_tools', sa.Column('company_name', sa.String(), nullable=True))
    
    # Create source tracking table
    op.create_table('source_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('new_tools_count', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_tracking_id'), 'source_tracking', ['id'], unique=False)
    op.create_index(op.f('ix_source_tracking_source_name'), 'source_tracking', ['source_name'], unique=True)

    # Create tool reports table for user feedback
    op.create_table('tool_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('report_type', sa.String(), nullable=False),  # 'dead_link', 'wrong_pricing', 'wrong_category'
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), default='pending', nullable=False),  # 'pending', 'resolved', 'rejected'
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['discovered_tools.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_reports_id'), 'tool_reports', ['id'], unique=False)
    op.create_index(op.f('ix_tool_reports_tool_id'), 'tool_reports', ['tool_id'], unique=False)

    # Add indexes for better performance
    op.create_index('ix_discovered_tools_website_status', 'discovered_tools', ['website_status'], unique=False)
    op.create_index('ix_discovered_tools_canonical_url', 'discovered_tools', ['canonical_url'], unique=False)
    op.create_index('ix_discovered_tools_confidence_score', 'discovered_tools', ['confidence_score'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_discovered_tools_confidence_score', table_name='discovered_tools')
    op.drop_index('ix_discovered_tools_canonical_url', table_name='discovered_tools')
    op.drop_index('ix_discovered_tools_website_status', table_name='discovered_tools')
    
    # Drop tables
    op.drop_index(op.f('ix_tool_reports_tool_id'), table_name='tool_reports')
    op.drop_index(op.f('ix_tool_reports_id'), table_name='tool_reports')
    op.drop_table('tool_reports')
    
    op.drop_index(op.f('ix_source_tracking_source_name'), table_name='source_tracking')
    op.drop_index(op.f('ix_source_tracking_id'), table_name='source_tracking')
    op.drop_table('source_tracking')
    
    # Remove columns from discovered_tools
    op.drop_column('discovered_tools', 'company_name')
    op.drop_column('discovered_tools', 'canonical_url')
    op.drop_column('discovered_tools', 'user_reports')
    op.drop_column('discovered_tools', 'website_status')
    op.drop_column('discovered_tools', 'last_health_check')