"""add_sector_and_rate_system

Revision ID: 002_add_sector_and_rate_system
Revises: 001_initial_schema
Create Date: 2026-09-10 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_sector_and_rate_system'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update source_files
    op.add_column('source_files', sa.Column('sector', sa.String(length=100), nullable=True, server_default="Building Works"))
    op.add_column('source_files', sa.Column('rate_system', sa.String(length=100), nullable=True, server_default="BSR"))
    op.execute("UPDATE source_files SET sector = 'Building Works' WHERE sector IS NULL")
    op.execute("UPDATE source_files SET rate_system = 'BSR' WHERE rate_system IS NULL")
    op.alter_column('source_files', 'sector', nullable=False)
    op.alter_column('source_files', 'rate_system', nullable=False)

    op.create_index('ix_source_files_sector', 'source_files', ['sector'])
    op.create_index('ix_source_files_rate_system', 'source_files', ['rate_system'])
    op.create_index('ix_source_files_sector_rate_system', 'source_files', ['sector', 'rate_system'])

    # 2. Update rate_items
    op.add_column('rate_items', sa.Column('sector', sa.String(length=100), nullable=True, server_default="Building Works"))
    op.add_column('rate_items', sa.Column('rate_system', sa.String(length=100), nullable=True, server_default="BSR"))
    op.execute("UPDATE rate_items SET sector = 'Building Works' WHERE sector IS NULL")
    op.execute("UPDATE rate_items SET rate_system = 'BSR' WHERE rate_system IS NULL")
    op.alter_column('rate_items', 'sector', nullable=False)
    op.alter_column('rate_items', 'rate_system', nullable=False)

    op.create_index('ix_rate_items_sector', 'rate_items', ['sector'])
    op.create_index('ix_rate_items_rate_system', 'rate_items', ['rate_system'])
    op.create_index('ix_rate_items_sector_rate_system', 'rate_items', ['sector', 'rate_system'])
    op.create_index('ix_rate_items_sector_prov_dist_year', 'rate_items', ['sector', 'province', 'district', 'year'])
    op.create_index('ix_rate_items_system_year_cat', 'rate_items', ['rate_system', 'year', 'category_name'])

    # 3. Update master_items
    op.add_column('master_items', sa.Column('sector', sa.String(length=100), nullable=True, server_default="Building Works"))
    op.add_column('master_items', sa.Column('rate_system', sa.String(length=100), nullable=True, server_default="BSR"))
    op.execute("UPDATE master_items SET sector = 'Building Works' WHERE sector IS NULL")
    op.execute("UPDATE master_items SET rate_system = 'BSR' WHERE rate_system IS NULL")
    op.alter_column('master_items', 'sector', nullable=False)

    op.create_index('ix_master_items_sector', 'master_items', ['sector'])
    op.create_index('ix_master_items_rate_system', 'master_items', ['rate_system'])


def downgrade() -> None:
    # 1. Revert master_items
    op.drop_index('ix_master_items_rate_system', table_name='master_items')
    op.drop_index('ix_master_items_sector', table_name='master_items')
    op.drop_column('master_items', 'rate_system')
    op.drop_column('master_items', 'sector')

    # 2. Revert rate_items
    op.drop_index('ix_rate_items_system_year_cat', table_name='rate_items')
    op.drop_index('ix_rate_items_sector_prov_dist_year', table_name='rate_items')
    op.drop_index('ix_rate_items_sector_rate_system', table_name='rate_items')
    op.drop_index('ix_rate_items_rate_system', table_name='rate_items')
    op.drop_index('ix_rate_items_sector', table_name='rate_items')
    op.drop_column('rate_items', 'rate_system')
    op.drop_column('rate_items', 'sector')

    # 3. Revert source_files
    op.drop_index('ix_source_files_sector_rate_system', table_name='source_files')
    op.drop_index('ix_source_files_rate_system', table_name='source_files')
    op.drop_index('ix_source_files_sector', table_name='source_files')
    op.drop_column('source_files', 'rate_system')
    op.drop_column('source_files', 'sector')
