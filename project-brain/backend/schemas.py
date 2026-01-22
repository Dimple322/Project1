from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Document schemas
class DocumentMetadata(BaseModel):
    source: str = ""
    author: Optional[str] = None
    created_date: Optional[str] = None

class DocumentBase(BaseModel):
    filename: str
    mime_type: str
    file_size: int
    doc_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    pass

class DocumentVersionSchema(BaseModel):
    id: str
    document_id: str
    version_number: int
    parsing_status: str
    chunk_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentSchema(DocumentBase):
    id: str
    sha256_hash: str
    original_path: str
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersionSchema] = []
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    parsing_status: str
    chunk_count: int
    created_at: datetime

# Chunk schemas
class ChunkBase(BaseModel):
    text_content: str
    page_number: Optional[int] = None
    section_path: Optional[str] = None

class ChunkSchema(ChunkBase):
    id: str
    document_id: str
    version_id: str
    chunk_number: int
    is_embedded: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Lexicon schemas
class LexiconBase(BaseModel):
    term: str
    canonical_form: str
    category: str  # abbreviation, synonym, term
    definition: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    source: str = "manual"
    confidence: float = 1.0

class LexiconCreate(LexiconBase):
    pass

class LexiconSchema(LexiconBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Transcript schemas
class TranscriptEdit(BaseModel):
    original: str
    corrected: str
    confidence: float

class TranscriptCorrectionRequest(BaseModel):
    document_id: str

class TranscriptCorrectionResponse(BaseModel):
    document_id: str
    original_text: str
    corrected_text: str
    diff: List[TranscriptEdit]
    correction_status: str

# Entity schemas
class EntityBase(BaseModel):
    name: str
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)

class ProjectCreate(EntityBase):
    description: Optional[str] = None

class ProjectSchema(ProjectCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PhaseCreate(EntityBase):
    project_id: str
    description: Optional[str] = None

class PhaseSchema(PhaseCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FacilityCreate(EntityBase):
    project_id: str
    description: Optional[str] = None

class FacilitySchema(FacilityCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class WellCreate(EntityBase):
    facility_id: str
    description: Optional[str] = None

class WellSchema(WellCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubsystemCreate(EntityBase):
    facility_id: str
    description: Optional[str] = None

class SubsystemSchema(SubsystemCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ContractorCreate(EntityBase):
    pass

class ContractorSchema(ContractorCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PersonCreate(EntityBase):
    role: Optional[str] = None

class PersonSchema(PersonCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Issue/Action/Decision schemas
class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "open"
    priority: Optional[str] = None
    subsystem_id: Optional[str] = None
    well_id: Optional[str] = None
    evidence_chunk_id: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: float = 1.0

class IssueSchema(IssueCreate):
    id: str
    is_pending_review: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActionItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "open"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    evidence_chunk_id: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: float = 1.0

class ActionItemSchema(ActionItemCreate):
    id: str
    is_pending_review: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class DecisionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    evidence_chunk_id: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: float = 1.0

class DecisionSchema(DecisionCreate):
    id: str
    is_pending_review: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Claim schemas
class ClaimCreate(BaseModel):
    subject_id: str
    subject_type: str
    claim_text: str
    evidence_chunk_id: Optional[str] = None
    evidence_quote: Optional[str] = None
    confidence: float = 1.0

class ClaimSchema(ClaimCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Curation schemas
class CurationEventCreate(BaseModel):
    event_type: str
    object_id: str
    object_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CurationEventSchema(CurationEventCreate):
    id: str
    applied: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Search schemas
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    page_number: Optional[int] = None
    section_path: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    limit: int
    offset: int

# Status Report schemas
class StatusCard(BaseModel):
    subject_id: str
    subject_type: str
    subject_name: str
    claims: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    last_updated: datetime

# Ingest schemas
class IngestResponse(BaseModel):
    document_id: str
    filename: str
    sha256_hash: str
    status: str
    message: str
