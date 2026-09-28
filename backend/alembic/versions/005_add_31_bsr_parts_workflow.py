"""add_31_bsr_parts_workflow

Revision ID: 005_add_31_bsr_parts_workflow
Revises: 004_add_cesmm_sl_sections
Create Date: 2026-09-28 10:10:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
from alembic import op
import sqlalchemy as sa

revision: str = '005_add_31_bsr_parts_workflow'
down_revision: Union[str, None] = '004_add_cesmm_sl_sections'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CANONICAL_BSR_PARTS_SEED = [
    {
        "part_no": "01",
        "part_code": "DM",
        "part_name": "Demolish Works",
        "aliases": "Demolisher, Demolition, Demolishing, DM",
        "description": "Demolition of existing walls, foundations, roofs, finishes, clearing and transporting debris",
        "sort_order": 1,
    },
    {
        "part_no": "02",
        "part_code": "EW",
        "part_name": "Earth Works",
        "aliases": "Earth Work, Excavator, Excavation, Trenching, Filling, EW",
        "description": "Site clearing, excavation in trenches/pits, earth filling, compaction, and disposal",
        "sort_order": 2,
    },
    {
        "part_no": "03",
        "part_code": "BK",
        "part_name": "Brick Works",
        "aliases": "Brick Layer, Brickwork, Brick Masonry, BK",
        "description": "Burnt clay brickwork in various mortar mixes, 112mm, 225mm and decorative brickwork",
        "sort_order": 3,
    },
    {
        "part_no": "04",
        "part_code": "CT",
        "part_name": "Concrete Works",
        "aliases": "Concreter, Concrete, Ready Mix, Mass Concrete, Reinforced Concrete, CT, CTR",
        "description": "Plain and reinforced in-situ concrete for foundations, columns, beams, slabs, and lintels",
        "sort_order": 4,
    },
    {
        "part_no": "05",
        "part_code": "FW",
        "part_name": "Form Works",
        "aliases": "Form Work, Shuttering, Formwork, Timber Shuttering, Steel Shutters, FW",
        "description": "Timber and steel shuttering/formwork for columns, beams, slabs, stairs, and foundations",
        "sort_order": 5,
    },
    {
        "part_no": "06",
        "part_code": "RF",
        "part_name": "Steel Rates",
        "aliases": "R/F Works, Reinforcement, Tor Steel, Mild Steel, Fabric Reinforcement, BRC Mesh, RF",
        "description": "High yield tor steel, mild steel reinforcement, cutting, bending, fabricating, and placing",
        "sort_order": 6,
    },
    {
        "part_no": "07",
        "part_code": "RR",
        "part_name": "R R Masonry Works",
        "aliases": "R R Masonry, Random Rubble, Rubble Masonry, Stone Masonry, RR",
        "description": "Random rubble stone masonry in foundation and superstructure using cement mortar",
        "sort_order": 7,
    },
    {
        "part_no": "08",
        "part_code": "CB",
        "part_name": "Cement Block Works",
        "aliases": "Cement Block Work, Blockwork, Solid Blocks, Hollow Blocks, Cellular Blocks, CB",
        "description": "Precast cement solid and hollow block masonry in walling and partitions",
        "sort_order": 8,
    },
    {
        "part_no": "09",
        "part_code": "PA",
        "part_name": "Pavior Works",
        "aliases": "Pavior, Paving, Floor Tiling, Wall Tiling, Terrazzo, Granito, Interlocking Paving, PA",
        "description": "Ceramic and porcelain tiling, terrazzo, non-slip paving, skirting, and interlocking blocks",
        "sort_order": 9,
    },
    {
        "part_no": "10",
        "part_code": "PL",
        "part_name": "Plasterer Works",
        "aliases": "Plasterer, Plastering, Rendering, Skim Coat, Wall Finishes, PL",
        "description": "Internal and external cement sand plastering, lime rendering, soffit plaster, and skim coating",
        "sort_order": 10,
    },
    {
        "part_no": "11",
        "part_code": "TN",
        "part_name": "Tinker Works",
        "aliases": "Tinker, Flashing, Zinc Aluminum Flashing, Guttering, Down Pipes, Valleys, Ridges, TN",
        "description": "Sheet metal work, zinc alum eaves gutters, flashing, valleys, downpipes, and rainwater accessories",
        "sort_order": 11,
    },
    {
        "part_no": "12",
        "part_code": "RO",
        "part_name": "Roof Works",
        "aliases": "Roofer, Roofing, Roof Covering, Asbestos Sheets, Zinc Alum Roofing, Clay Tiles, RO",
        "description": "Corrugated asbestos sheets, zinc-alum sheets, roofing tiles, insulation, and roof accessories",
        "sort_order": 12,
    },
    {
        "part_no": "13",
        "part_code": "CP",
        "part_name": "Carpenter & Joiner Works",
        "aliases": "Carpenter, Joiner, Carpentry, Timber Framing, Doors, Windows, Ceiling, Woodwork, CP",
        "description": "Timber roof frameworks, panelled doors, sashes, timber ceilings, partitions, and joinery fittings",
        "sort_order": 13,
    },
    {
        "part_no": "14",
        "part_code": "IR",
        "part_name": "Iron Monger Works",
        "aliases": "Iron Monger, Structural Steel, Steel Trusses, Grills, Railings, Gates, IR",
        "description": "Structural steel roof trusses, purlins, MS window grills, iron gates, railings, and metal hardware",
        "sort_order": 14,
    },
    {
        "part_no": "15",
        "part_code": "BF",
        "part_name": "Brass Founder Works",
        "aliases": "Brass Founder, Door Ironmongery, Hinges, Locks, Tower Bolts, Handles, BF",
        "description": "Door and window ironmongery, brass and stainless steel butt hinges, mortise locks, handles, bolts",
        "sort_order": 15,
    },
    {
        "part_no": "16",
        "part_code": "PT",
        "part_name": "Painter Works",
        "aliases": "Painter, Painting, Emulsion Paint, Enamel Paint, Weather Shield, Varnishing, PT",
        "description": "Internal emulsion, exterior weather shield, enamel paint on timber and metal, and wood preservative",
        "sort_order": 16,
    },
    {
        "part_no": "17",
        "part_code": "PB",
        "part_name": "Plumber Works",
        "aliases": "Plumber, Plumbing, Sanitary Fittings, Commode, Wash Basin, Taps, Showers, PB",
        "description": "Sanitary ware, water closets, wash basins, bib taps, ball valves, shower fittings, and internal plumbing",
        "sort_order": 17,
    },
    {
        "part_no": "18",
        "part_code": "MA",
        "part_name": "Maintenance Works",
        "aliases": "Maintenance, Repairs, Servicing, Rehabilitation, Renovations, MA",
        "description": "General maintenance, routine minor repairs, replacement of damaged components, and servicing",
        "sort_order": 18,
    },
    {
        "part_no": "19",
        "part_code": "TG",
        "part_name": "Tempered Glass Works",
        "aliases": "Tempered Glass, Toughened Glass, Frameless Glass Partitions, Glass Doors, TG",
        "description": "10mm/12mm frameless tempered glass shop fronts, shower screens, spider fittings, and glass doors",
        "sort_order": 19,
    },
    {
        "part_no": "20",
        "part_code": "GL",
        "part_name": "Glazier Works",
        "aliases": "Glazier, Glazing, Sheet Glass, Frosted Glass, Louver Blades, Putty Glazing, GL",
        "description": "5mm/6mm clear and tinted sheet glass for window sashes, louver blades, fanlights, and bead glazing",
        "sort_order": 20,
    },
    {
        "part_no": "21",
        "part_code": "CL",
        "part_name": "Cladding Works",
        "aliases": "Cladding, Aluminium Composite Panels, ACP Cladding, Wall Panelling, CL",
        "description": "Aluminium composite panel (ACP) external facade cladding, sub-framing, silicone sealant, and wall panelling",
        "sort_order": 21,
    },
    {
        "part_no": "22",
        "part_code": "GW",
        "part_name": "General Works",
        "aliases": "General Work, Sundries, Miscellaneous General, Clearing, Scaffolding, GW",
        "description": "General site requirements, scaffolding, temporary works, clearing site, and sundry construction services",
        "sort_order": 22,
    },
    {
        "part_no": "23",
        "part_code": "AL",
        "part_name": "Maintenance Aluminum Works",
        "aliases": "Maintenance Aluminum, Aluminum Repair, Servicing Aluminum, AL",
        "description": "Repairs, realignment, gasket replacement, roller replacement, and maintenance of aluminum fabrications",
        "sort_order": 23,
    },
    {
        "part_no": "24",
        "part_code": "ALN",
        "part_name": "Natural Anodized Aluminum Works",
        "aliases": "Natural Anodized Aluminum, NA Aluminum, Silver Aluminum Partitions, Doors, Windows, ALN",
        "description": "Natural anodized aluminum shop fronts, sliding/casement windows, glazed partitions, and louvers",
        "sort_order": 24,
    },
    {
        "part_no": "25",
        "part_code": "ALB",
        "part_name": "Bronze Anodized Aluminum Works",
        "aliases": "Bronze Anodized Aluminum, BA Aluminum, Bronze Aluminum Doors, Windows, Partitions, ALB",
        "description": "Bronze anodized aluminum framing for doors, windows, glazed curtain walls, and internal office partitions",
        "sort_order": 25,
    },
    {
        "part_no": "26",
        "part_code": "ALP",
        "part_name": "Powder Coated Aluminum Works",
        "aliases": "Powder Coated Aluminum, PC Aluminum, Color Aluminum Doors, Windows, Partitions, ALP",
        "description": "Electrostatic powder coated aluminum extrusions, casement/sliding windows, heavy-duty glazed doors",
        "sort_order": 26,
    },
    {
        "part_no": "27",
        "part_code": "EL",
        "part_name": "Electrical Works",
        "aliases": "Electrical, Wiring, Conduits, Distribution Boards, Lighting Points, Power Outlets, EL",
        "description": "Surface and concealed conduit wiring, light points, socket outlets, distribution boards, and fittings",
        "sort_order": 27,
    },
    {
        "part_no": "28",
        "part_code": "DR",
        "part_name": "Drainage Works",
        "aliases": "Drainage, Drain Layer, Sewerage, Stormwater, Gulley, Manholes, Catchpits, DR",
        "description": "Surface water drains, uPVC/clay sewer pipes, inspection chambers, brick manholes, and septic tanks",
        "sort_order": 28,
    },
    {
        "part_no": "29",
        "part_code": "RD",
        "part_name": "Road Works",
        "aliases": "Road Work, Highway, Roads, Kerbs, Asphalt, Macadam, Subbase, RD",
        "description": "Road excavation, dense graded aggregate base, prime coat, asphalt concrete surfacing, and road kerbs",
        "sort_order": 29,
    },
    {
        "part_no": "30",
        "part_code": "WF",
        "part_name": "Water Supply Works",
        "aliases": "Water Supply, Water Mains, Pipe Laying, Water Fittings, Valves, WF, W",
        "description": "External water supply distribution, HDPE/DI/uPVC pressure pipe mains, sluice valves, and water meters",
        "sort_order": 30,
    },
    {
        "part_no": "31",
        "part_code": "PR",
        "part_name": "Preliminaries & Miscellaneous Works",
        "aliases": "Preliminaries, Miscellaneous, General Notes, Provisional Sums, Testing, Site Facilities, PR, MS",
        "description": "Contractor preliminaries, temporary site sheds, water/electricity for works, testing, and provisional sums",
        "sort_order": 31,
    },
]

def upgrade() -> None:
    # 1. Create canonical_bsr_parts table
    parts_table = op.create_table(
        'canonical_bsr_parts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_no', sa.String(length=10), nullable=False),
        sa.Column('part_code', sa.String(length=20), nullable=False),
        sa.Column('part_name', sa.String(length=255), nullable=False),
        sa.Column('aliases', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_canonical_bsr_parts_part_no', 'canonical_bsr_parts', ['part_no'], unique=True)
    op.create_index('ix_canonical_bsr_parts_part_code', 'canonical_bsr_parts', ['part_code'], unique=False)
    op.create_index('ix_canonical_bsr_parts_sort_order', 'canonical_bsr_parts', ['sort_order'], unique=False)
    op.create_index('ix_canonical_bsr_parts_active', 'canonical_bsr_parts', ['active'], unique=False)

    # 2. Add columns to rate_items
    op.add_column('rate_items', sa.Column('canonical_part_id', sa.Integer(), nullable=True))
    op.add_column('rate_items', sa.Column('part_mapping_status', sa.String(length=40), server_default='UNMAPPED', nullable=True))
    op.create_foreign_key('fk_rate_items_canonical_part', 'rate_items', 'canonical_bsr_parts', ['canonical_part_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_rate_items_canonical_part_id', 'rate_items', ['canonical_part_id'])
    op.create_index('ix_rate_items_part_mapping_status', 'rate_items', ['part_mapping_status'])

    # 3. Add columns to bsr_books
    op.add_column('bsr_books', sa.Column('period', sa.String(length=50), server_default='Annual', nullable=True))
    op.add_column('bsr_books', sa.Column('vat_basis', sa.String(length=80), server_default='Without VAT', nullable=True))
    op.add_column('bsr_books', sa.Column('source_authority', sa.String(length=255), nullable=True))

    # 4. Add columns to bsr_items
    op.add_column('bsr_items', sa.Column('canonical_part_id', sa.Integer(), nullable=True))
    op.add_column('bsr_items', sa.Column('source_page', sa.Integer(), nullable=True))
    op.add_column('bsr_items', sa.Column('source_sheet', sa.String(length=255), nullable=True))
    op.add_column('bsr_items', sa.Column('source_row', sa.Integer(), nullable=True))
    op.add_column('bsr_items', sa.Column('source_raw_text', sa.Text(), nullable=True))
    op.add_column('bsr_items', sa.Column('validation_status', sa.String(length=40), server_default='VALID', nullable=True))
    op.add_column('bsr_items', sa.Column('part_mapping_status', sa.String(length=40), server_default='UNMAPPED', nullable=True))
    op.create_foreign_key('fk_bsr_items_canonical_part', 'bsr_items', 'canonical_bsr_parts', ['canonical_part_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_bsr_items_canonical_part_id', 'bsr_items', ['canonical_part_id'])

    # 5. Add columns to master_items
    op.add_column('master_items', sa.Column('canonical_part_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_master_items_canonical_part', 'master_items', 'canonical_bsr_parts', ['canonical_part_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_master_items_canonical_part_id', 'master_items', ['canonical_part_id'])

    # 6. Add columns to item_matches
    op.add_column('item_matches', sa.Column('match_score', sa.Float(), server_default='1.0', nullable=True))
    op.add_column('item_matches', sa.Column('match_method', sa.String(length=50), server_default='CODE_EXACT', nullable=True))
    op.add_column('item_matches', sa.Column('approved', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('item_matches', sa.Column('approved_by', sa.String(length=255), nullable=True))

    # 7. Create project_part_selections table
    op.create_table(
        'project_part_selections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('canonical_part_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), server_default='Selected Part BOQ', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['canonical_part_id'], ['canonical_bsr_parts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_part_selections_canonical_part_id', 'project_part_selections', ['canonical_part_id'])
    op.create_index('ix_project_part_selections_project_id', 'project_part_selections', ['project_id'])

    # 8. Create project_part_items table
    op.create_table(
        'project_part_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_part_selection_id', sa.Integer(), nullable=False),
        sa.Column('bsr_item_id', sa.Integer(), nullable=True),
        sa.Column('master_item_id', sa.Integer(), nullable=True),
        sa.Column('item_no', sa.String(length=50), nullable=True),
        sa.Column('original_code', sa.String(length=100), nullable=True),
        sa.Column('project_code', sa.String(length=100), nullable=True),
        sa.Column('original_description', sa.Text(), nullable=False),
        sa.Column('project_description', sa.Text(), nullable=False),
        sa.Column('original_unit', sa.String(length=50), nullable=False),
        sa.Column('project_unit', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('original_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('adjustment_percent', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('adopted_rate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('amount', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('rate_source_year', sa.String(length=50), nullable=False),
        sa.Column('rate_source_book', sa.String(length=255), nullable=True),
        sa.Column('rate_source_province', sa.String(length=100), nullable=True),
        sa.Column('rate_source_district', sa.String(length=100), nullable=True),
        sa.Column('rate_source_revision', sa.String(length=120), nullable=True),
        sa.Column('rate_source_file_id', sa.Integer(), nullable=True),
        sa.Column('rate_source_page', sa.Integer(), nullable=True),
        sa.Column('rate_source_sheet', sa.String(length=255), nullable=True),
        sa.Column('rate_source_row', sa.Integer(), nullable=True),
        sa.Column('rate_justification', sa.Text(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_modified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('unit_warning_acknowledged', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('edited_by', sa.String(length=255), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['bsr_item_id'], ['rate_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['master_item_id'], ['master_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_part_selection_id'], ['project_part_selections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_part_items_selection_id', 'project_part_items', ['project_part_selection_id'])
    op.create_index('ix_project_part_items_bsr_item_id', 'project_part_items', ['bsr_item_id'])
    op.create_index('ix_project_part_items_master_item_id', 'project_part_items', ['master_item_id'])
    op.create_index('ix_project_part_items_rate_source_year', 'project_part_items', ['rate_source_year'])

    # 9. Create project_part_item_history table (Section 21 Edit History)
    op.create_table(
        'project_part_item_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_part_item_id', sa.Integer(), nullable=False),
        sa.Column('field_changed', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(length=255), nullable=True),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_part_item_id'], ['project_part_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_part_item_history_item_id', 'project_part_item_history', ['project_part_item_id'])

    # 10. Create part_template_mappings table
    op.create_table(
        'part_template_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('canonical_part_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('target_sheet', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('start_row', sa.Integer(), server_default='5', nullable=False),
        sa.Column('item_no_column', sa.String(length=10), server_default='A', nullable=True),
        sa.Column('bsr_ref_column', sa.String(length=10), server_default='B', nullable=True),
        sa.Column('description_column', sa.String(length=10), server_default='C', nullable=True),
        sa.Column('unit_column', sa.String(length=10), server_default='D', nullable=True),
        sa.Column('qty_column', sa.String(length=10), server_default='E', nullable=True),
        sa.Column('original_rate_column', sa.String(length=10), server_default='F', nullable=True),
        sa.Column('adopted_rate_column', sa.String(length=10), server_default='G', nullable=True),
        sa.Column('amount_column', sa.String(length=10), server_default='H', nullable=True),
        sa.Column('rate_year_column', sa.String(length=10), server_default='I', nullable=True),
        sa.Column('rate_source_column', sa.String(length=10), server_default='J', nullable=True),
        sa.Column('justification_column', sa.String(length=10), server_default='K', nullable=True),
        sa.Column('remarks_column', sa.String(length=10), server_default='L', nullable=True),
        sa.Column('column_mapping_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['canonical_part_id'], ['canonical_bsr_parts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_part_template_mappings_canonical_part_id', 'part_template_mappings', ['canonical_part_id'])

    # Seed the 31 canonical BSR parts
    op.bulk_insert(parts_table, CANONICAL_BSR_PARTS_SEED)


def downgrade() -> None:
    op.drop_table('part_template_mappings')
    op.drop_table('project_part_item_history')
    op.drop_table('project_part_items')
    op.drop_table('project_part_selections')
    op.drop_constraint('fk_item_matches_master_item', 'item_matches', type_='foreignkey')
    op.drop_column('item_matches', 'approved_by')
    op.drop_column('item_matches', 'approved')
    op.drop_column('item_matches', 'match_method')
    op.drop_column('item_matches', 'match_score')
    op.drop_constraint('fk_master_items_canonical_part', 'master_items', type_='foreignkey')
    op.drop_column('master_items', 'canonical_part_id')
    op.drop_constraint('fk_bsr_items_canonical_part', 'bsr_items', type_='foreignkey')
    op.drop_column('bsr_items', 'part_mapping_status')
    op.drop_column('bsr_items', 'validation_status')
    op.drop_column('bsr_items', 'source_raw_text')
    op.drop_column('bsr_items', 'source_row')
    op.drop_column('bsr_items', 'source_sheet')
    op.drop_column('bsr_items', 'source_page')
    op.drop_column('bsr_items', 'canonical_part_id')
    op.drop_column('bsr_books', 'source_authority')
    op.drop_column('bsr_books', 'vat_basis')
    op.drop_column('bsr_books', 'period')
    op.drop_constraint('fk_rate_items_canonical_part', 'rate_items', type_='foreignkey')
    op.drop_column('rate_items', 'part_mapping_status')
    op.drop_column('rate_items', 'canonical_part_id')
    op.drop_table('canonical_bsr_parts')
