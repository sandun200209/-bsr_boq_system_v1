"""add_cesmm_sl_sections

Revision ID: 004_add_cesmm_sl_sections
Revises: 003_auth_roles_cloud
Create Date: 2026-09-23 13:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
from alembic import op
import sqlalchemy as sa

revision: str = '004_add_cesmm_sl_sections'
down_revision: Union[str, None] = '003_auth_roles_cloud'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CESMM_SECTIONS = [
    {"section_no": "01", "section_code": "A", "name": "Preliminaries"},
    {"section_no": "02", "section_code": "B", "name": "Ground investigation"},
    {"section_no": "03", "section_code": "C", "name": "Geotechnical and other specialist processes"},
    {"section_no": "04", "section_code": "D", "name": "Demolition and site clearance"},
    {"section_no": "05", "section_code": "E", "name": "Earth works"},
    {"section_no": "06", "section_code": "F", "name": "Dredging and reclamation"},
    {"section_no": "07", "section_code": "G", "name": "Landscaping and irrigation"},
    {"section_no": "08", "section_code": "H1", "name": "Concrete work - Insitu concrete"},
    {"section_no": "09", "section_code": "H2", "name": "Concrete work - Form work"},
    {"section_no": "10", "section_code": "H3", "name": "Concrete work - Reinforcement"},
    {"section_no": "11", "section_code": "H4", "name": "Concrete work - Precast concrete"},
    {"section_no": "12", "section_code": "J1", "name": "Pipe work - Pipes"},
    {"section_no": "13", "section_code": "J2", "name": "Pipe work - Fittings"},
    {"section_no": "14", "section_code": "J3", "name": "Pipe work - Valves and miscellaneous work"},
    {"section_no": "15", "section_code": "J4", "name": "Pipe work - Manholes and pipe work ancillaries"},
    {"section_no": "16", "section_code": "J5", "name": "Pipe work - Supports and protection, ancillaries to laying and excavation"},
    {"section_no": "17", "section_code": "K", "name": "Structural metalwork"},
    {"section_no": "18", "section_code": "L", "name": "Miscellaneous metalwork"},
    {"section_no": "19", "section_code": "M", "name": "Timber"},
    {"section_no": "20", "section_code": "N1", "name": "Piling work - Piling"},
    {"section_no": "21", "section_code": "N2", "name": "Piling work - Diaphragm walling"},
    {"section_no": "22", "section_code": "N3", "name": "Piling work - Underpinning"},
    {"section_no": "23", "section_code": "P", "name": "Roads and paving"},
    {"section_no": "24", "section_code": "Q", "name": "Rail track"},
    {"section_no": "25", "section_code": "R", "name": "Tunnels"},
    {"section_no": "26", "section_code": "S", "name": "Brickwork, block work and masonry"},
    {"section_no": "27", "section_code": "T", "name": "Painting"},
    {"section_no": "28", "section_code": "U", "name": "Waterproofing"},
    {"section_no": "29", "section_code": "V", "name": "Miscellaneous work"},
    {"section_no": "30", "section_code": "W", "name": "Sewer and water main renovation and ancillary works"},
    {"section_no": "31", "section_code": "X", "name": "Simple building works incidental to civil engineering works"},
]

def upgrade() -> None:
    # 1. Create cesmm_sections table
    cesmm_table = op.create_table(
        'cesmm_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section_no', sa.String(length=10), nullable=False),
        sa.Column('section_code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cesmm_sections_section_no', 'cesmm_sections', ['section_no'], unique=True)
    op.create_index('ix_cesmm_sections_section_code', 'cesmm_sections', ['section_code'], unique=False)

    # 2. Create rate_item_cesmm_sections table
    op.create_table(
        'rate_item_cesmm_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rate_item_id', sa.Integer(), nullable=False),
        sa.Column('cesmm_section_id', sa.Integer(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cesmm_section_id'], ['cesmm_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rate_item_id'], ['rate_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rate_item_id', 'cesmm_section_id', name='uq_rate_item_cesmm_section')
    )
    op.create_index('ix_rate_item_cesmm_sections_rate_item_id', 'rate_item_cesmm_sections', ['rate_item_id'], unique=False)
    op.create_index('ix_rate_item_cesmm_sections_cesmm_section_id', 'rate_item_cesmm_sections', ['cesmm_section_id'], unique=False)
    op.create_index('ix_rate_item_cesmm_lookup', 'rate_item_cesmm_sections', ['rate_item_id', 'cesmm_section_id'], unique=False)

    # 3. Seed the 31 exact CESMM-SL sections
    now = datetime.utcnow()
    seed_data = [
        {
            "section_no": item["section_no"],
            "section_code": item["section_code"],
            "name": item["name"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        for item in CESMM_SECTIONS
    ]
    op.bulk_insert(cesmm_table, seed_data)


def downgrade() -> None:
    op.drop_table('rate_item_cesmm_sections')
    op.drop_table('cesmm_sections')
