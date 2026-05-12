"""Initial migration - users, teams, team_members, user_sessions, user_project_permissions tables

Revision ID: 0001_initial_migration
Revises: 
Create Date: 2026-05-12 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False, default=1),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)

    op.create_table(
        'teams',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_teams_owner_id'), 'teams', ['owner_id'], unique=False)

    op.create_table(
        'team_members',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('team_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, default='member'),
        sa.Column('invited_by', sa.BigInteger(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_team_members_team_id'), 'team_members', ['team_id'], unique=False)
    op.create_index(op.f('ix_team_members_user_id'), 'team_members', ['user_id'], unique=False)

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('refresh_token', sa.String(length=500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('device_type', sa.String(length=20), nullable=True),
        sa.Column('is_revoked', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_user_sessions_token'), 'user_sessions', ['token'], unique=True)

    op.create_table(
        'user_project_permissions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('granted_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'project_id'),
        mysql_engine='InnoDB'
    )
    op.create_index(op.f('ix_user_project_permissions_user_id'), 'user_project_permissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_project_permissions_project_id'), 'user_project_permissions', ['project_id'], unique=False)

def downgrade() -> None:
    op.drop_table('user_project_permissions')
    op.drop_table('user_sessions')
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('users')
