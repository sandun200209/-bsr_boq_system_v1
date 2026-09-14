"""auth_roles_cloud

Revision ID: 003_auth_roles_cloud
Revises: 002_add_sector_and_rate_system
Create Date: 2026-09-14 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_auth_roles_cloud'
down_revision: Union[str, None] = '002_add_sector_and_rate_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='USER', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)

    # 2. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=80), nullable=False),
        sa.Column('entity_type', sa.String(length=80), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_user_email', 'audit_logs', ['user_email'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # 3. Add cloud storage and user tracking to source_files
    op.add_column('source_files', sa.Column('storage_provider', sa.String(length=50), server_default='local', nullable=False))
    op.add_column('source_files', sa.Column('storage_key', sa.String(length=500), nullable=True))
    op.add_column('source_files', sa.Column('public_url', sa.String(length=1000), nullable=True))
    op.add_column('source_files', sa.Column('uploaded_by_id', sa.Integer(), nullable=True))
    op.add_column('source_files', sa.Column('uploaded_by_email', sa.String(length=255), nullable=True))
    op.create_foreign_key('fk_source_files_uploaded_by_id', 'source_files', 'users', ['uploaded_by_id'], ['id'], ondelete='SET NULL')

    # 4. Add author tracking to rate_items & master_items
    op.add_column('rate_items', sa.Column('updated_by_email', sa.String(length=255), nullable=True))
    op.add_column('master_items', sa.Column('updated_by_email', sa.String(length=255), nullable=True))

    # 5. Insert default seed users
    # Passwords:
    # admin@bsrhub.lk: Admin@123456
    # manager@bsrhub.lk: Manager@123456
    # qs@bsrhub.lk: User@123456
    # viewer@bsrhub.lk: Viewer@123456
    op.execute("""
        INSERT INTO users (email, username, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES 
        ('admin@bsrhub.lk', 'admin', '$2b$10$X55Hn1CvOMVlkh99P2Z/BOS8ZbTzNh48NF5wQHY3ElXhHaGK6m1Zy', 'System Administrator', 'ADMIN', true, NOW(), NOW()),
        ('manager@bsrhub.lk', 'manager', '$2b$10$2u..vMizRgwkrckhE8owYORCVXGMm7U1kb.EGqfSXhs27eB88Ww4C', 'Project Manager', 'MANAGER', true, NOW(), NOW()),
        ('qs@bsrhub.lk', 'qs_engineer', '$2b$10$MGyB1nQzESjgXRMBkrLFcOIZmkDoClrIkYG5P/H58iQMGwbFaT3Pe', 'Quantity Surveyor', 'USER', true, NOW(), NOW()),
        ('viewer@bsrhub.lk', 'viewer', '$2b$10$fgGdV5S87ASUKctheVeDHO2k6yz.h.oHamegU2TTOEdKKGGg6s1Y2', 'Executive Viewer', 'VIEWER', true, NOW(), NOW())
        ON CONFLICT (email) DO NOTHING;
    """)

    # Record initial audit entry
    op.execute("""
        INSERT INTO audit_logs (user_email, action, entity_type, entity_id, description, created_at)
        VALUES ('system', 'SYSTEM_UPGRADE', 'SYSTEM', '003', 'Upgraded to Multi-Device Cloud & Auth System (Alembic 003)', NOW());
    """)


def downgrade() -> None:
    op.drop_column('master_items', 'updated_by_email')
    op.drop_column('rate_items', 'updated_by_email')
    op.drop_constraint('fk_source_files_uploaded_by_id', 'source_files', type_='foreignkey')
    op.drop_column('source_files', 'uploaded_by_email')
    op.drop_column('source_files', 'uploaded_by_id')
    op.drop_column('source_files', 'public_url')
    op.drop_column('source_files', 'storage_key')
    op.drop_column('source_files', 'storage_provider')
    op.drop_table('audit_logs')
    op.drop_table('users')
