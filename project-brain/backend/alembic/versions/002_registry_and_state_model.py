"""Add registry, state model, and rules engine tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Registry Entities - Canonical knowledge base
    op.create_table(
        'registry_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_key', sa.String(255), nullable=False),
        sa.Column('entity_key', sa.String(255), nullable=False),  # slug/code
        sa.Column('type', sa.String(50), nullable=False),  # facility, well, subsystem, contractor, person, phase, workpackage
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('aliases', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('attributes', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='active'),  # active, archived, deprecated, pending
        sa.Column('owner_person_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['registry_entities.id']),
        sa.UniqueConstraint('project_key', 'type', 'entity_key', name='uq_registry_entity_key'),
        sa.UniqueConstraint('project_key', 'type', 'canonical_name', name='uq_registry_canonical_name'),
    )
    op.create_index('ix_registry_entities_project_key', 'registry_entities', ['project_key'])
    op.create_index('ix_registry_entities_type', 'registry_entities', ['type'])
    op.create_index('ix_registry_entities_status', 'registry_entities', ['status'])
    op.create_index('ix_registry_entities_parent_id', 'registry_entities', ['parent_id'])

    # Registry Relations
    op.create_table(
        'registry_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_key', sa.String(255), nullable=False),
        sa.Column('from_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('to_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),  # PART_OF, OWNED_BY, DEPENDS_ON, RELATED_TO, AFFECTS, MANAGES
        sa.Column('attributes', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('source', sa.String(50), nullable=True, server_default='manual'),  # manual, system, inferred
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_entity_id'], ['registry_entities.id']),
        sa.ForeignKeyConstraint(['to_entity_id'], ['registry_entities.id']),
        sa.UniqueConstraint('from_entity_id', 'to_entity_id', 'relation_type', name='uq_registry_relation'),
    )
    op.create_index('ix_registry_relations_project_key', 'registry_relations', ['project_key'])
    op.create_index('ix_registry_relations_from_entity_id', 'registry_relations', ['from_entity_id'])
    op.create_index('ix_registry_relations_to_entity_id', 'registry_relations', ['to_entity_id'])
    op.create_index('ix_registry_relations_type', 'registry_relations', ['relation_type'])

    # Registry Constraints - Rules for entity management
    op.create_table(
        'registry_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_key', sa.String(255), nullable=False),
        sa.Column('constraint_key', sa.String(255), nullable=False),
        sa.Column('constraint_type', sa.String(50), nullable=False),  # entity_type, required_fields, unique_fields, cardinality
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_key', 'constraint_key', name='uq_registry_constraint'),
    )
    op.create_index('ix_registry_constraints_project_key', 'registry_constraints', ['project_key'])

    # Document Page Blocks - PDF structure
    op.create_table(
        'doc_page_blocks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doc_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('block_type', sa.String(50), nullable=False),  # text, table, figure, heading, paragraph
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('bbox', postgresql.JSONB(), nullable=True),  # {x0, y0, x1, y1}
        sa.Column('block_order', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['doc_version_id'], ['document_versions.id']),
    )
    op.create_index('ix_doc_page_blocks_doc_version', 'doc_page_blocks', ['doc_version_id'])
    op.create_index('ix_doc_page_blocks_page_number', 'doc_page_blocks', ['page_number'])
    op.create_index('ix_doc_page_blocks_type', 'doc_page_blocks', ['block_type'])

    # Page Anchors - Detected objects on pages
    op.create_table(
        'page_anchors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doc_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('anchor_text', sa.String(255), nullable=False),
        sa.Column('bbox', postgresql.JSONB(), nullable=True),
        sa.Column('registry_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('source', sa.String(50), nullable=False, server_default='system'),  # system, manual, ocr, regex
        sa.Column('detection_method', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['doc_version_id'], ['document_versions.id']),
        sa.ForeignKeyConstraint(['registry_entity_id'], ['registry_entities.id']),
    )
    op.create_index('ix_page_anchors_doc_version', 'page_anchors', ['doc_version_id'])
    op.create_index('ix_page_anchors_registry_entity', 'page_anchors', ['registry_entity_id'])
    op.create_index('ix_page_anchors_page_number', 'page_anchors', ['page_number'])

    # Table Attachments - Link tables to objects
    op.create_table(
        'table_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doc_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('block_id', postgresql.UUID(as_uuid=True), nullable=False),  # doc_page_blocks.id
        sa.Column('registry_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('anchor_id', postgresql.UUID(as_uuid=True), nullable=True),  # page_anchors.id
        sa.Column('source', sa.String(50), nullable=False, server_default='system'),  # system, manual
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['doc_version_id'], ['document_versions.id']),
        sa.ForeignKeyConstraint(['block_id'], ['doc_page_blocks.id']),
        sa.ForeignKeyConstraint(['registry_entity_id'], ['registry_entities.id']),
        sa.ForeignKeyConstraint(['anchor_id'], ['page_anchors.id']),
    )
    op.create_index('ix_table_attachments_doc_version', 'table_attachments', ['doc_version_id'])
    op.create_index('ix_table_attachments_registry_entity', 'table_attachments', ['registry_entity_id'])
    op.create_index('ix_table_attachments_block_id', 'table_attachments', ['block_id'])

    # Curation Rules - System learns from corrections
    op.create_table(
        'curation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_key', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),  # LINK_FIX, PARSING_ANCHOR, LEXICON_NORMALIZATION, CLAIM_OVERRIDE, PARSING_RULE
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default=50),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('created_from_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('test_cases', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_from_event_id'], ['curation_events.id']),
    )
    op.create_index('ix_curation_rules_project_key', 'curation_rules', ['project_key'])
    op.create_index('ix_curation_rules_type', 'curation_rules', ['rule_type'])
    op.create_index('ix_curation_rules_priority', 'curation_rules', ['priority', 'enabled'])

    # Object State - Current status of project objects
    op.create_table(
        'object_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('registry_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('state_json', postgresql.JSONB(), nullable=False),
        sa.Column('computed_from', postgresql.JSONB(), nullable=True),  # {claim_ids, item_ids, rule_ids}
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['registry_entity_id'], ['registry_entities.id']),
        sa.UniqueConstraint('registry_entity_id', 'as_of_date', name='uq_object_state_per_date'),
    )
    op.create_index('ix_object_state_registry_entity', 'object_state', ['registry_entity_id'])
    op.create_index('ix_object_state_as_of_date', 'object_state', ['as_of_date'])

    # State Conflicts - Competing claims
    op.create_table(
        'state_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('registry_entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_path', sa.String(255), nullable=False),  # e.g., "progress_percent", "expected_completion_date"
        sa.Column('competing_claim_ids', postgresql.JSONB(), nullable=False),
        sa.Column('conflict_values', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),  # open, resolved
        sa.Column('resolution_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['registry_entity_id'], ['registry_entities.id']),
        sa.ForeignKeyConstraint(['resolution_event_id'], ['curation_events.id']),
    )
    op.create_index('ix_state_conflicts_registry_entity', 'state_conflicts', ['registry_entity_id'])
    op.create_index('ix_state_conflicts_status', 'state_conflicts', ['status'])

    # Update chunks table to include anchor info
    op.add_column('chunks', sa.Column('anchor_entity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('chunks', sa.Column('table_attachment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('chunks', sa.Column('block_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_chunks_anchor_entity', 'chunks', 'registry_entities', ['anchor_entity_id'], ['id'])
    op.create_foreign_key('fk_chunks_table_attachment', 'chunks', 'table_attachments', ['table_attachment_id'], ['id'])
    op.create_foreign_key('fk_chunks_doc_page_block', 'chunks', 'doc_page_blocks', ['block_id'], ['id'])


def downgrade():
    op.drop_table('state_conflicts')
    op.drop_table('object_state')
    op.drop_table('curation_rules')
    op.drop_table('table_attachments')
    op.drop_table('page_anchors')
    op.drop_table('doc_page_blocks')
    op.drop_table('registry_constraints')
    op.drop_table('registry_relations')
    op.drop_table('registry_entities')
    
    op.drop_constraint('fk_chunks_anchor_entity', 'chunks', type_='foreignkey')
    op.drop_constraint('fk_chunks_table_attachment', 'chunks', type_='foreignkey')
    op.drop_constraint('fk_chunks_doc_page_block', 'chunks', type_='foreignkey')
    op.drop_column('chunks', 'anchor_entity_id')
    op.drop_column('chunks', 'table_attachment_id')
    op.drop_column('chunks', 'block_id')
