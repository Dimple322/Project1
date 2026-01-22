"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create all tables
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('original_path', sa.String(512), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('doc_metadata', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha256_hash', name='uq_sha256')
    )
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])

    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('parsed_path', sa.String(512), nullable=True),
        sa.Column('parsing_status', sa.String(50), nullable=False),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('parsing_metadata', postgresql.JSON(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'version_number', name='uq_doc_version')
    )
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index('ix_document_versions_parsing_status', 'document_versions', ['parsing_status'])
    op.create_index('ix_document_versions_created_at', 'document_versions', ['created_at'])

    op.create_table(
        'chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('version_id', sa.String(36), nullable=False),
        sa.Column('chunk_number', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_path', sa.String(512), nullable=True),
        sa.Column('embedding_vector_id', sa.String(36), nullable=True),
        sa.Column('is_embedded', sa.Boolean(), nullable=False),
        sa.Column('chunk_metadata', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_version_id', 'chunks', ['version_id'])
    op.create_index('ix_chunks_page_number', 'chunks', ['page_number'])
    op.create_index('ix_chunks_is_embedded', 'chunks', ['is_embedded'])
    op.create_index('idx_doc_version_chunk', 'chunks', ['document_id', 'version_id', 'chunk_number'])

    op.create_table(
        'lexicon',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('term', sa.String(255), nullable=False),
        sa.Column('canonical_form', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('term', name='uq_term')
    )
    op.create_index('ix_lexicon_term', 'lexicon', ['term'])

    op.create_table(
        'transcript_corrections',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('corrected_text', sa.Text(), nullable=False),
        sa.Column('diff', postgresql.JSON(), nullable=False),
        sa.Column('correction_status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transcript_corrections_document_id', 'transcript_corrections', ['document_id'])

    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_project_name'),
        sa.UniqueConstraint('canonical_name', name='uq_project_canonical')
    )
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])

    op.create_table(
        'phases',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'canonical_name', name='uq_project_phase')
    )
    op.create_index('ix_phases_project_id', 'phases', ['project_id'])

    op.create_table(
        'facilities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'canonical_name', name='uq_project_facility')
    )
    op.create_index('ix_facilities_project_id', 'facilities', ['project_id'])

    op.create_table(
        'wells',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('facility_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facility_id', 'canonical_name', name='uq_facility_well')
    )
    op.create_index('ix_wells_facility_id', 'wells', ['facility_id'])

    op.create_table(
        'subsystems',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('facility_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facility_id', 'canonical_name', name='uq_facility_subsystem')
    )
    op.create_index('ix_subsystems_facility_id', 'subsystems', ['facility_id'])

    op.create_table(
        'contractors',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_contractor_name'),
        sa.UniqueConstraint('canonical_name', name='uq_contractor_canonical')
    )

    op.create_table(
        'persons',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('canonical_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('attributes', postgresql.JSON(), nullable=False),
        sa.Column('aliases', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_name', name='uq_person_canonical')
    )
    op.create_index('ix_persons_name', 'persons', ['name'])

    op.create_table(
        'issues',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('subsystem_id', sa.String(36), nullable=True),
        sa.Column('well_id', sa.String(36), nullable=True),
        sa.Column('evidence_chunk_id', sa.String(36), nullable=True),
        sa.Column('evidence_quote', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_pending_review', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subsystem_id'], ['subsystems.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['well_id'], ['wells.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_chunk_id'], ['chunks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_issues_status', 'issues', ['status'])
    op.create_index('ix_issues_subsystem_id', 'issues', ['subsystem_id'])
    op.create_index('ix_issues_well_id', 'issues', ['well_id'])
    op.create_index('ix_issues_is_pending_review', 'issues', ['is_pending_review'])

    op.create_table(
        'action_items',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('assigned_to', sa.String(36), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('evidence_chunk_id', sa.String(36), nullable=True),
        sa.Column('evidence_quote', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_pending_review', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to'], ['persons.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_chunk_id'], ['chunks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_action_items_status', 'action_items', ['status'])
    op.create_index('ix_action_items_is_pending_review', 'action_items', ['is_pending_review'])

    op.create_table(
        'decisions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('evidence_chunk_id', sa.String(36), nullable=True),
        sa.Column('evidence_quote', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_pending_review', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_chunk_id'], ['chunks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decisions_is_pending_review', 'decisions', ['is_pending_review'])

    op.create_table(
        'claims',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('subject_id', sa.String(36), nullable=False),
        sa.Column('subject_type', sa.String(50), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('evidence_chunk_id', sa.String(36), nullable=True),
        sa.Column('evidence_quote', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_chunk_id'], ['chunks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_claims_subject_id', 'claims', ['subject_id'])
    op.create_index('ix_claims_subject_type', 'claims', ['subject_type'])
    op.create_index('idx_subject_claim', 'claims', ['subject_id', 'subject_type'])

    op.create_table(
        'curation_events',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('object_id', sa.String(36), nullable=False),
        sa.Column('object_type', sa.String(50), nullable=False),
        sa.Column('metadata', postgresql.JSON(), nullable=False),
        sa.Column('applied', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_curation_events_event_type', 'curation_events', ['event_type'])
    op.create_index('ix_curation_events_object_id', 'curation_events', ['object_id'])
    op.create_index('ix_curation_events_applied', 'curation_events', ['applied'])

    op.create_table(
        'entity_mentions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('chunk_id', sa.String(36), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('mention_text', sa.String(255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_entity_mentions_chunk_id', 'entity_mentions', ['chunk_id'])
    op.create_index('ix_entity_mentions_entity_id', 'entity_mentions', ['entity_id'])
    op.create_index('ix_entity_mentions_entity_type', 'entity_mentions', ['entity_type'])

    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('object_id', sa.String(36), nullable=False),
        sa.Column('object_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tasks_task_type', 'tasks', ['task_type'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('idx_status_type', 'tasks', ['status', 'task_type'])

def downgrade():
    op.drop_table('tasks')
    op.drop_table('entity_mentions')
    op.drop_table('curation_events')
    op.drop_table('claims')
    op.drop_table('decisions')
    op.drop_table('action_items')
    op.drop_table('issues')
    op.drop_table('persons')
    op.drop_table('contractors')
    op.drop_table('subsystems')
    op.drop_table('wells')
    op.drop_table('facilities')
    op.drop_table('phases')
    op.drop_table('projects')
    op.drop_table('transcript_corrections')
    op.drop_table('lexicon')
    op.drop_table('chunks')
    op.drop_table('document_versions')
    op.drop_table('documents')
