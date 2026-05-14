"""Add project management tables

Revision ID: 0002_add_project_tables
Revises: 0001_initial_migration
Create Date: 2026-05-12 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '0002_add_project_tables'
down_revision = '0001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.BigInteger(), nullable=True),
        sa.Column('template_type', sa.String(length=20), nullable=False, server_default='blank'),
        sa.Column('template_id', sa.BigInteger(), nullable=True),
        sa.Column('target_platforms', mysql.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('config', mysql.JSON(), nullable=True),
        sa.Column('project_data', mysql.JSON(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_edited_by', sa.BigInteger(), nullable=True),
        sa.Column('last_edited_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['last_edited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_index(op.f('ix_projects_team_id'), 'projects', ['team_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)

    # Create pages table
    op.create_table(
        'pages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('path', sa.String(length=200), nullable=False),
        sa.Column('is_home', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('layout_config', mysql.JSON(), nullable=True),
        sa.Column('components', mysql.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'path'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_pages_project_id'), 'pages', ['project_id'], unique=False)

    # Create page_states table
    op.create_table(
        'page_states',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('page_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('data_type', sa.String(length=20), nullable=False),
        sa.Column('default_value', mysql.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_page_states_page_id'), 'page_states', ['page_id'], unique=False)

    # Create project_snapshots table
    op.create_table(
        'project_snapshots',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('version_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('snapshot_data', mysql.JSON(), nullable=False),
        sa.Column('project_version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_project_snapshots_project_id'), 'project_snapshots', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_snapshots_created_at'), 'project_snapshots', ['created_at'], unique=False)

    # Create project_shares table
    op.create_table(
        'project_shares',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('share_token', sa.String(length=100), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False, server_default='view'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_password_protected', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('copy_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_views', sa.Integer(), nullable=True),
        sa.Column('max_copies', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_project_shares_project_id'), 'project_shares', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_shares_share_token'), 'project_shares', ['share_token'], unique=True)
    op.create_index(op.f('ix_project_shares_expires_at'), 'project_shares', ['expires_at'], unique=False)

    # Create project_collaborators table
    op.create_table(
        'project_collaborators',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False, server_default='write'),
        sa.Column('invited_by', sa.BigInteger(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_project_collaborators_project_id'), 'project_collaborators', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_collaborators_user_id'), 'project_collaborators', ['user_id'], unique=False)

    # Create project_templates table
    op.create_table(
        'project_templates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('template_data', mysql.JSON(), nullable=False),
        sa.Column('target_platforms', mysql.JSON(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_project_templates_category'), 'project_templates', ['category'], unique=False)
    op.create_index(op.f('ix_project_templates_is_public'), 'project_templates', ['is_public'], unique=False)


def downgrade() -> None:
    op.drop_table('project_templates')
    op.drop_table('project_collaborators')
    op.drop_table('project_shares')
    op.drop_table('project_snapshots')
    op.drop_table('page_states')
    op.drop_table('pages')
    op.drop_table('projects')
