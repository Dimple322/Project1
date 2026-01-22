from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, Float, Text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    original_path = Column(String(512), nullable=False)  # MinIO path
    sha256_hash = Column(String(64), nullable=False, unique=True, index=True)
    doc_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    parsed_path = Column(String(512), nullable=True)  # MinIO path to parsed.json
    parsing_status = Column(String(50), default="pending", index=True)  # pending, parsing, completed, failed
    parsing_error = Column(Text, nullable=True)
    parsing_metadata = Column(JSON, default={})
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    document = relationship("Document", back_populates="versions")
    chunks = relationship("Chunk", back_populates="version", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True, index=True)
    section_path = Column(String(512), nullable=True)  # e.g., "Chapter1/Section2/Subsection3"
    embedding_vector_id = Column(String(36), nullable=True)  # Qdrant point_id
    is_embedded = Column(Boolean, default=False, index=True)
    chunk_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")
    version = relationship("DocumentVersion", back_populates="chunks")
    
    __table_args__ = (
        Index("idx_doc_version_chunk", "document_id", "version_id", "chunk_number"),
    )

class Lexicon(Base):
    __tablename__ = "lexicon"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    term = Column(String(255), nullable=False, unique=True, index=True)
    canonical_form = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # abbreviation, synonym, term
    definition = Column(Text, nullable=True)
    aliases = Column(JSON, default=[])  # List of alternative forms
    source = Column(String(50), nullable=False)  # auto, manual
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TranscriptCorrection(Base):
    __tablename__ = "transcript_corrections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    diff = Column(JSON, default=[])  # List of edits with confidence
    correction_status = Column(String(50), default="completed")  # completed, pending_review
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    canonical_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Phase(Base):
    __tablename__ = "phases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_id", "canonical_name", name="uq_project_phase"),
    )

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_id", "canonical_name", name="uq_project_facility"),
    )

class Well(Base):
    __tablename__ = "wells"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("facility_id", "canonical_name", name="uq_facility_well"),
    )

class Subsystem(Base):
    __tablename__ = "subsystems"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("facility_id", "canonical_name", name="uq_facility_subsystem"),
    )

class Contractor(Base):
    __tablename__ = "contractors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    canonical_name = Column(String(255), nullable=False, unique=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

class Person(Base):
    __tablename__ = "persons"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    canonical_name = Column(String(255), nullable=False, unique=True)
    role = Column(String(100), nullable=True)
    attributes = Column(JSON, default={})
    aliases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open", index=True)  # open, closed, pending
    priority = Column(String(20), nullable=True)  # high, medium, low
    subsystem_id = Column(String(36), ForeignKey("subsystems.id", ondelete="SET NULL"), nullable=True, index=True)
    well_id = Column(String(36), ForeignKey("wells.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    evidence_quote = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    is_pending_review = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open", index=True)  # open, in_progress, completed
    assigned_to = Column(String(36), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    evidence_chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    evidence_quote = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    is_pending_review = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    evidence_chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    evidence_quote = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    is_pending_review = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = Column(String(36), nullable=False, index=True)  # subsystem_id, well_id, facility_id
    subject_type = Column(String(50), nullable=False, index=True)  # subsystem, well, facility
    claim_text = Column(Text, nullable=False)
    evidence_chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    evidence_quote = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_subject_claim", "subject_id", "subject_type"),
    )

class CurationEvent(Base):
    __tablename__ = "curation_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)
    # Types: LINK_FIX, ENTITY_MERGE, LEXICON_ADD, CLAIM_OVERRIDE, PARSING_RULE_ADD
    object_id = Column(String(36), nullable=False, index=True)
    object_type = Column(String(50), nullable=False)
    event_metadata = Column(JSON, default={})
    applied = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EntityMention(Base):
    __tablename__ = "entity_mentions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    mention_text = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(50), nullable=False, index=True)  # parse, embed, rerank, extract_meeting
    object_id = Column(String(36), nullable=False, index=True)
    object_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    task_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_status_type", "status", "task_type"),
    )

# ===== REGISTRY MODELS (NEW) =====

class RegistryEntity(Base):
    """Canonical knowledge base for project entities"""
    __tablename__ = "registry_entities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_key = Column(String(255), nullable=False, index=True)
    entity_key = Column(String(255), nullable=False)  # slug/code
    type = Column(String(50), nullable=False, index=True)  # facility, well, subsystem, contractor, person, phase, workpackage
    canonical_name = Column(String(255), nullable=False)
    aliases = Column(JSON, default=[])
    attributes = Column(JSON, default={})
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active", index=True)  # active, archived, deprecated, pending
    owner_person_id = Column(String(36), nullable=True)
    parent_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    children = relationship("RegistryEntity", remote_side=[id])
    
    __table_args__ = (
        UniqueConstraint("project_key", "type", "entity_key", name="uq_registry_entity_key"),
        UniqueConstraint("project_key", "type", "canonical_name", name="uq_registry_canonical_name"),
    )

class RegistryRelation(Base):
    """Relations between registry entities"""
    __tablename__ = "registry_relations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_key = Column(String(255), nullable=False, index=True)
    from_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    to_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False, index=True)  # PART_OF, OWNED_BY, DEPENDS_ON, RELATED_TO, AFFECTS, MANAGES
    attributes = Column(JSON, default={})
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="manual")  # manual, system, inferred
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("from_entity_id", "to_entity_id", "relation_type", name="uq_registry_relation"),
    )

class RegistryConstraint(Base):
    """Rules for entity management"""
    __tablename__ = "registry_constraints"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_key = Column(String(255), nullable=False, index=True)
    constraint_key = Column(String(255), nullable=False)
    constraint_type = Column(String(50), nullable=False)  # entity_type, required_fields, unique_fields, cardinality
    payload = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("project_key", "constraint_key", name="uq_registry_constraint"),
    )

class DocPageBlock(Base):
    """PDF page structure (text, tables, figures)"""
    __tablename__ = "doc_page_blocks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    block_type = Column(String(50), nullable=False, index=True)  # text, table, figure, heading, paragraph
    text_content = Column(Text, nullable=True)
    bbox = Column(JSON, nullable=True)  # {x0, y0, x1, y1}
    block_order = Column(Integer, nullable=False)
    block_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class PageAnchor(Base):
    """Detected objects on pages"""
    __tablename__ = "page_anchors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    anchor_text = Column(String(255), nullable=False)
    bbox = Column(JSON, nullable=True)
    registry_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="system", index=True)  # system, manual, ocr, regex
    detection_method = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TableAttachment(Base):
    """Link tables to objects"""
    __tablename__ = "table_attachments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    block_id = Column(String(36), ForeignKey("doc_page_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    registry_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="SET NULL"), nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    anchor_id = Column(String(36), ForeignKey("page_anchors.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(50), default="system")  # system, manual
    created_at = Column(DateTime, default=datetime.utcnow)

class CurationRule(Base):
    """Rules learned from corrections"""
    __tablename__ = "curation_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_key = Column(String(255), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)  # LINK_FIX, PARSING_ANCHOR, LEXICON_NORMALIZATION, CLAIM_OVERRIDE, PARSING_RULE
    payload = Column(JSON, nullable=False)
    priority = Column(Integer, default=50, index=True)
    enabled = Column(Boolean, default=True, index=True)
    created_from_event_id = Column(String(36), ForeignKey("curation_events.id", ondelete="SET NULL"), nullable=True)
    test_cases = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ObjectState(Base):
    """Current status of project objects"""
    __tablename__ = "object_state"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registry_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    as_of_date = Column(DateTime, nullable=False, index=True)
    state_json = Column(JSON, nullable=False)
    computed_from = Column(JSON, nullable=True)  # {claim_ids, item_ids, rule_ids}
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("registry_entity_id", "as_of_date", name="uq_object_state_per_date"),
    )

class StateConflict(Base):
    """Competing claims about object state"""
    __tablename__ = "state_conflicts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registry_entity_id = Column(String(36), ForeignKey("registry_entities.id", ondelete="CASCADE"), nullable=False, index=True)
    field_path = Column(String(255), nullable=False)
    competing_claim_ids = Column(JSON, nullable=False)
    conflict_values = Column(JSON, nullable=False)
    status = Column(String(50), default="open", index=True)  # open, resolved
    resolution_event_id = Column(String(36), ForeignKey("curation_events.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
