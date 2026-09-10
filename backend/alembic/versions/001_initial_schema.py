"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-09 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enable pg_trgm extension if on postgres
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 2. Source Files
    op.create_table(
        'source_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('province', sa.String(length=80), nullable=False),
        sa.Column('district', sa.String(length=80), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('revision', sa.String(length=120), nullable=False),
        sa.Column('dataset_type', sa.String(length=80), nullable=False, server_default="BSR Rate Book"),
        sa.Column('vat_basis', sa.String(length=80), nullable=False, server_default="Without VAT"),
        sa.Column('category_hint', sa.String(length=120), nullable=True),
        sa.Column('upload_status', sa.String(length=40), nullable=False, server_default="UPLOADED"),
        sa.Column('import_status', sa.String(length=40), nullable=False, server_default="READY_FOR_REVIEW"),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('total_rows_detected', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('valid_rows', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('review_rows', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('rejected_rows', sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_filename')
    )
    op.create_index('ix_source_files_sha256', 'source_files', ['sha256_hash'])
    op.create_index('ix_source_files_province', 'source_files', ['province'])
    op.create_index('ix_source_files_year', 'source_files', ['year'])

    # 3. Import Jobs
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_file_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False, server_default="UPLOADED"),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(['source_file_id'], ['source_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_jobs_source_file_id', 'import_jobs', ['source_file_id'])

    # 4. Master Items
    op.create_table(
        'master_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_code', sa.String(length=80), nullable=False),
        sa.Column('canonical_description', sa.Text(), nullable=False),
        sa.Column('canonical_unit', sa.String(length=40), nullable=False),
        sa.Column('category', sa.String(length=160), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('master_code')
    )
    op.create_index('ix_master_items_code', 'master_items', ['master_code'])

    # 5. Rate Items
    op.create_table(
        'rate_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_file_id', sa.Integer(), nullable=False),
        sa.Column('province', sa.String(length=80), nullable=False),
        sa.Column('district', sa.String(length=80), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('revision', sa.String(length=120), nullable=False),
        sa.Column('dataset_type', sa.String(length=80), nullable=False, server_default="BSR Rate Book"),
        sa.Column('vat_basis', sa.String(length=80), nullable=False, server_default="Without VAT"),
        sa.Column('category_code', sa.String(length=80), nullable=True),
        sa.Column('category_name', sa.String(length=160), nullable=True),
        sa.Column('item_code', sa.String(length=80), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(length=40), nullable=True),
        sa.Column('rate', sa.Float(), nullable=True),
        sa.Column('master_item_id', sa.Integer(), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_sheet', sa.String(length=160), nullable=True),
        sa.Column('source_row', sa.Integer(), nullable=True),
        sa.Column('source_cell', sa.String(length=80), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default="1.0"),
        sa.Column('validation_status', sa.String(length=40), nullable=False, server_default="VALID"),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['master_item_id'], ['master_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_file_id'], ['source_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rate_items_source_file_id', 'rate_items', ['source_file_id'])
    op.create_index('ix_rate_items_item_code', 'rate_items', ['item_code'])
    op.create_index('ix_rate_items_status', 'rate_items', ['validation_status'])
    op.create_index('ix_rates_lookup', 'rate_items', ['province', 'district', 'year', 'revision', 'category_name'])
    
    # Trigram Indexes for high-speed live search
    op.execute("CREATE INDEX IF NOT EXISTS ix_rates_desc_trgm ON rate_items USING gin (description gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rates_code_trgm ON rate_items USING gin (item_code gin_trgm_ops)")

    # 6. Rate Item Master Mapping
    op.create_table(
        'rate_item_master_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_item_id', sa.Integer(), nullable=False),
        sa.Column('rate_item_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default="1.0"),
        sa.Column('mapped_by', sa.String(length=80), nullable=False, server_default="user"),
        sa.Column('mapped_at', sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(['master_item_id'], ['master_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rate_item_id'], ['rate_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rate_item_id')
    )
    op.create_index('ix_mapping_master_id', 'rate_item_master_mapping', ['master_item_id'])

def downgrade() -> None:
    op.drop_table('rate_item_master_mapping')
    op.drop_table('rate_items')
    op.drop_table('master_items')
    op.drop_table('import_jobs')
    op.drop_table('source_files')
