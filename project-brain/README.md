# Project Brain ??

**AI-powered document analysis and entity management system** for project intelligence, built with a DB-first architecture.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Development Guide](#development-guide)
- [Database Migrations](#database-migrations)
- [Troubleshooting](#troubleshooting)

## Overview

Project Brain is a comprehensive document analysis system designed for complex project environments (oil & gas, construction, etc.). It leverages:

- **Document Ingestion Pipeline**: Automatic file upload ? parsing ? chunking ? embedding
- **Intelligent Search**: Semantic search with BF-M3 embeddings + BGE-Reranker-v2-m3 reranking
- **Transcript Processing**: Automatic correction using lexicon, meeting item extraction
- **Entity Management**: Projects, Facilities, Wells, Subsystems, Persons, Contractors
- **Issue/Action/Decision Tracking**: Extracted from documents with evidence and confidence scores
- **Curation Layer**: Track all edits (LINK_FIX, ENTITY_MERGE, LEXICON_ADD, CLAIM_OVERRIDE, PARSING_RULE_ADD)
- **Status Reports**: Comprehensive status cards with claims, issues, actions, decisions
- **Graph Visualization**: Neo4j backend for entity relationship visualization (optional)

## Architecture

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | PostgreSQL 15 | Primary relational store (DB-first design) |
| **Cache/Queue** | Redis 7 | Task queue for async jobs, caching |
| **Vector DB** | Qdrant | Document embeddings storage & semantic search |
| **Graph DB** | Neo4j 5 | Entity relationships (optional) |
| **Object Storage** | MinIO | Original files, parsed JSON, embeddings |
| **Backend** | FastAPI + SQLAlchemy | REST API, ORM, database abstraction |
| **Worker** | Celery | Async task processing (parsing, embedding, extraction) |
| **Frontend** | Next.js 14 + React | Modern web UI |
| **Inference** | LM Studio (local) | Local LLM for entity linking (optional) |

### Data Flow

```
???????????????????????????????????????????????????????????????????
?                    USER UPLOADS DOCUMENT                         ?
???????????????????????????????????????????????????????????????????
                             ?
                    ??????????????????
                    ? POST /ingest   ?
                    ??????????????????
                             ?
                ??????????????????????????????
                ? Save original to MinIO     ?
                ? Compute SHA256 (idempotent)?
                ? Create Document record     ?
                ??????????????????????????????
                             ?
                    ??????????????????
                    ? Trigger parse  ? (Celery Task)
                    ??????????????????
                             ?
           ???????????????????????????????????
           ?                                  ?
    ????????????????              ????????????????????
    ? Docling      ? or fallback  ? Unstructured     ?
    ? (PDF/Office) ???????????????? (fallback)       ?
    ????????????????              ????????????????????
           ?                              ?
        ????????????????????????????????????
        ? Extract chunks with:             ?
        ? - text_content                   ?
        ? - page_number                    ?
        ? - section_path                   ?
        ????????????????????????????????????
                       ?
        ????????????????????????????????????
        ? Save parsed.json to MinIO        ?
        ? Create Chunk records in DB       ?
        ????????????????????????????????????
                       ?
              ???????????????????
              ? Trigger embed   ? (Celery Task)
              ???????????????????
                       ?
        ????????????????????????????????????
        ? BGE-M3 local embeddings          ?
        ? (1024-dim vectors)               ?
        ????????????????????????????????????
                       ?
        ????????????????????????????????????
        ? Upsert to Qdrant with payload:   ?
        ? - doc_id, version_id, chunk_id   ?
        ? - page_number, section_path      ?
        ????????????????????????????????????
                       ?
        ????????????????????????????????????
        ? Document fully indexed! ?        ?
        ? Ready for search & extraction    ?
        ????????????????????????????????????

SEARCH FLOW:
????????????????????????
? Query string         ?
????????????????????????
           ?
????????????????????????????????
? BGE-M3 embed query (1024-dim)?
????????????????????????????????
           ?
????????????????????????????????
? Qdrant semantic search       ?
? (COSINE distance, top-20)    ?
????????????????????????????????
           ?
????????????????????????????????
? BGE-Reranker-v2-m3           ?
? (Rerank to top-10)           ?
????????????????????????????????
           ?
????????????????????????????????
? Return ranked results        ?
? with scores & evidence       ?
????????????????????????????????

TRANSCRIPT FLOW (if document is transcript):
????????????????????????????
? Document tagged          ?
? as transcript            ?
????????????????????????????
           ?
????????????????????????????????
? Trigger transcript_correct   ? (Celery)
? (uses Lexicon table)         ?
????????????????????????????????
           ?
????????????????????????????????
? Apply corrections:           ?
? - abbrev ? full form         ?
? - synonym ? canonical        ?
? Track diffs with confidence  ?
????????????????????????????????
           ?
????????????????????????????????
? Save to TranscriptCorrection ?
? (original, corrected, diff)  ?
????????????????????????????????
           ?
????????????????????????????????
? Trigger extract_meeting      ? (Celery)
????????????????????????????????
           ?
????????????????????????????????
? Extract from corrected text: ?
? - Issues (keyword detect)    ?
? - ActionItems (assign, due)  ?
? - Decisions (resolved)       ?
? - Questions (ask)            ?
? All marked as pending_review ?
????????????????????????????????
           ?
????????????????????????????????
? Save to Issues, ActionItems, ?
? Decisions with evidence      ?
? (chunk_id, quote, confidence)?
????????????????????????????????
```

## Prerequisites

### Required
- **Docker & Docker Compose** (v20.10+)
- **Python 3.11** (for local development)
- **Node.js 18+** (for local UI development)
- **4GB RAM** minimum, **8GB recommended**
- **10GB disk space** (for containers + data)

### Optional but Recommended
- **LM Studio** (for local LLM inference, download from https://lmstudio.ai)
- **Git** for version control

## Quick Start

### Option 1: Full Docker Setup (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd project-brain

# Start all services
docker-compose up -d

# Wait for services to be healthy (check logs)
docker-compose logs -f

# Initialize database (in a new terminal)
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python seed_data.py

# Access services
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Qdrant: http://localhost:6333/dashboard
# MinIO: http://localhost:9001 (admin/admin)
# Neo4j: http://localhost:7474 (neo4j/neo4j_password)
```

### Option 2: Local Development

**Backend:**
```bash
cd project-brain/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL, Redis, etc. with docker
docker-compose up postgres redis qdrant minio -d

# Run migrations
python -m alembic upgrade head

# Seed data
python seed_data.py

# Start FastAPI server
python main.py

# Start Celery worker (new terminal)
celery -A celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd project-brain/ui

# Install dependencies
npm install

# Start dev server
npm run dev

# Open http://localhost:3000
```

## Project Structure

```
project-brain/
??? docker-compose.yml              # Full stack orchestration
??? README.md                        # This file
?
??? backend/                         # FastAPI Backend
?   ??? main.py                      # FastAPI app & routes
?   ??? db.py                        # Database connection
?   ??? config.py                    # Settings & environment
?   ??? logger.py                    # Logging setup
?   ??? models.py                    # SQLAlchemy models (DB-first)
?   ??? schemas.py                   # Pydantic schemas for API
?   ??? storage.py                   # MinIO client
?   ??? parsing.py                   # Document parsing (Docling + Unstructured)
?   ??? embeddings.py                # BGE-M3 embeddings & BGE-Reranker
?   ??? transcript_corrector.py      # Transcript correction via Lexicon
?   ??? meeting_extractor.py         # Extract issues/actions/decisions
?   ??? celery_app.py                # Async tasks (parse, embed, correct, extract)
?   ??? seed_data.py                 # Demo data script
?   ??? requirements.txt             # Python dependencies
?   ??? Dockerfile                   # Backend container
?   ??? .env                         # Environment variables
?   ??? alembic.ini                  # Migration config
?   ??? alembic/
?       ??? env.py                   # Migration environment
?       ??? versions/
?           ??? 001_initial_schema.py # Initial schema
?
??? ui/                              # Next.js Frontend
?   ??? app/                         # Pages & layouts
?   ?   ??? page.tsx                 # Home page
?   ?   ??? layout.tsx               # Root layout
?   ?   ??? globals.css              # Global styles
?   ?   ??? documents/page.tsx       # Documents page
?   ?   ??? search/page.tsx          # Search page
?   ?   ??? pending-review/page.tsx  # Pending review page
?   ?   ??? reports/page.tsx         # Status reports page
?   ?   ??? entities/page.tsx        # Entity management
?   ??? components/                  # React components
?   ?   ??? Navbar.tsx               # Navigation bar
?   ?   ??? DocumentUpload.tsx       # File upload
?   ?   ??? DocumentList.tsx         # Document listing
?   ?   ??? SearchComponent.tsx      # Search interface
?   ??? lib/                         # Utilities
?   ?   ??? api.ts                   # API client (axios)
?   ?   ??? hooks.ts                 # Custom React hooks
?   ??? package.json                 # Dependencies
?   ??? tsconfig.json                # TypeScript config
?   ??? tailwind.config.js           # Tailwind CSS config
?   ??? next.config.js               # Next.js config
?   ??? Dockerfile                   # UI container
```

## Features

### 1. Document Ingestion
- ? Upload PDF, DOCX, TXT files
- ? Automatic SHA256 hashing for idempotency
- ? Store originals in MinIO
- ? Trigger async parsing

### 2. Parsing Pipeline
- ? **Primary**: Docling (PDF + Office documents)
- ? **Fallback**: Unstructured
- ? Extract chunks with page numbers & section paths
- ? Save parsed.json to MinIO

### 3. Embedding & Search
- ? BGE-M3 local embeddings (1024-dim)
- ? Qdrant vector storage with payload
- ? Semantic search with reranking
- ? BGE-Reranker-v2-m3 for relevance ranking

### 4. Transcript Processing
- ? Mark documents as transcripts
- ? Auto-correct using Lexicon
- ? Track corrections with confidence
- ? Extract meeting items:
  - Issues
  - Action Items
  - Decisions
  - Questions

### 5. Entity Management
- ? Projects
- ? Phases
- ? Facilities
- ? Wells
- ? Subsystems
- ? Contractors
- ? Persons
- ? Canonical names + aliases
- ? JSONB attributes

### 6. Lexicon System
- ? Terms (with definitions)
- ? Abbreviations (e.g., BOP ? Blowout Preventer)
- ? Synonyms (e.g., 3-Phase Sep ? Three-Phase Separator)
- ? Auto-populate from documents
- ? Manual entry
- ? Confidence scores

### 7. Curation Layer
- ? Track all edits:
  - LINK_FIX: Correct entity references
  - ENTITY_MERGE: Merge duplicate entities
  - LEXICON_ADD: Add new terms
  - CLAIM_OVERRIDE: Override extracted claims
  - PARSING_RULE_ADD: Add custom parsing rules
- ? Non-destructive (never overwrite originals)
- ? Apply in subsequent processing runs

### 8. Reports
- ? Status Cards for Facility/Well/Subsystem
- ? Aggregate claims, issues, actions, decisions
- ? Include citations & evidence
- ? Last updated timestamps

### 9. Pending Review
- ? Review extracted items before approval
- ? Confidence scores for each item
- ? Approve or reject
- ? Filter by type and status

### 10. Frontend UI
- ? Responsive design (Tailwind CSS)
- ? Document upload with progress
- ? Document listing with status
- ? Semantic search interface
- ? Entity management forms
- ? Pending review dashboard
- ? Status report generation
- ? Graph visualization (Cytoscape integration ready)

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Document Management
```bash
# Upload document
POST /ingest/file
Content-Type: multipart/form-data
{file: <binary>}

# List documents
GET /documents?skip=0&limit=10

# Get document details
GET /documents/{document_id}
```

#### Search
```bash
# Search documents
POST /search
{
  "query": "pump failure symptoms",
  "limit": 10,
  "offset": 0,
  "filters": {}
}

Response:
{
  "results": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "text": "...",
      "score": 0.92,
      "page_number": 5,
      "section_path": "Chapter1/Section2"
    }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

#### Lexicon Management
```bash
# Create lexicon entry
POST /lexicon
{
  "term": "ESP",
  "canonical_form": "Electrical Submersible Pump",
  "category": "abbreviation",
  "aliases": ["E.S.P", "esp pump"],
  "definition": "...",
  "source": "manual",
  "confidence": 1.0
}

# List lexicon
GET /lexicon?skip=0&limit=10&category=abbreviation
```

#### Entity Management
```bash
# Create project
POST /entities/projects
{
  "name": "North Sea Platform",
  "canonical_name": "north_sea_platform",
  "aliases": ["NSP", "Platform A"],
  "attributes": {"location": "North Sea", "depth": "150m"}
}

# Create facility
POST /entities/facilities
{
  "project_id": "...",
  "name": "Production Platform",
  "canonical_name": "production_platform",
  "aliases": ["PP", "Main Platform"]
}

# Create well
POST /entities/wells
{
  "facility_id": "...",
  "name": "Well A-01",
  "canonical_name": "well_a_01",
  "aliases": ["A01", "Alpha-01"]
}

# Create subsystem
POST /entities/subsystems
{
  "facility_id": "...",
  "name": "Pump System",
  "canonical_name": "pump_system",
  "aliases": ["PS", "Main Pump"]
}
```

#### Issues/Actions/Decisions
```bash
# Create issue
POST /issues
{
  "title": "Pump vibration detected",
  "description": "High frequency vibration in main pump",
  "status": "open",
  "priority": "high",
  "subsystem_id": "...",
  "evidence_chunk_id": "...",
  "evidence_quote": "...",
  "confidence": 0.95
}

# List issues (with filters)
GET /issues?status=open&is_pending_review=true

# Create action item
POST /actions
{
  "title": "Schedule pump maintenance",
  "status": "open",
  "assigned_to": "person_id",
  "due_date": "2024-02-01T00:00:00",
  "confidence": 0.8
}

# Create decision
POST /decisions
{
  "title": "Replace pump unit",
  "description": "Decision to replace entire pump unit",
  "rationale": "Age and wear analysis",
  "confidence": 0.9
}
```

#### Pending Review
```bash
# List pending items
GET /pending-review

Response:
{
  "issues": [...],
  "actions": [...],
  "decisions": [...],
  "total": 15
}

# Approve item
POST /pending-review/approve/{item_type}/{item_id}

# Reject item
DELETE /pending-review/{item_type}/{item_id}
```

#### Curation
```bash
# Record curation event
POST /curation/event
{
  "event_type": "ENTITY_MERGE",
  "object_id": "entity_id",
  "object_type": "project",
  "metadata": {
    "merged_with": "other_entity_id",
    "reason": "Duplicate entity"
  }
}

# List curation events
GET /curation/events?event_type=ENTITY_MERGE&applied=false
```

#### Reports
```bash
# Get status card
GET /reports/status/facility/{facility_id}
GET /reports/status/subsystem/{subsystem_id}
GET /reports/status/well/{well_id}

Response:
{
  "subject_id": "...",
  "subject_type": "facility",
  "subject_name": "Production Platform A",
  "claims": [...],
  "issues": [...],
  "actions": [...],
  "decisions": [...],
  "last_updated": "2024-01-15T10:30:00"
}
```

#### Transcript Processing
```bash
# Trigger transcript correction
POST /transcript/correct
{
  "document_id": "..."
}

# Get corrected transcript
GET /transcript/{document_id}

Response:
{
  "document_id": "...",
  "original_text": "BOP failure detected",
  "corrected_text": "Blowout Preventer failure detected",
  "diff": [
    {
      "original": "BOP",
      "corrected": "Blowout Preventer",
      "confidence": 1.0
    }
  ],
  "correction_status": "completed"
}
```

#### Health Check
```bash
GET /health

Response:
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00",
  "version": "0.1.0"
}
```

## Database Migrations

### Create Database
```bash
# Migrations are auto-applied on docker-compose up
# Or manually:
docker-compose exec backend python -m alembic upgrade head
```

### Create Migration
```bash
# Add new migration for schema changes
cd backend
python -m alembic revision --autogenerate -m "Add new table"

# Review generated migration in alembic/versions/
# Apply it
python -m alembic upgrade head
```

### Database Schema (Key Tables)

**documents**: Original files with SHA256 hash (idempotency key)
**document_versions**: Parsed versions with parsing status
**chunks**: Text segments with page_number, section_path, embedding_vector_id
**lexicon**: Terms, abbreviations, synonyms with confidence
**transcript_corrections**: Original ? corrected with diff
**projects, phases, facilities, wells, subsystems**: Entity registry
**contractors, persons**: Additional entities
**issues, action_items, decisions**: Extracted items with evidence
**claims**: Subject-specific statements with citations
**curation_events**: Audit trail of all manual edits
**entity_mentions**: Links between chunks and entities
**tasks**: Background job queue (parse, embed, correct, extract)

## Seed Data

Pre-populated demo data includes:

```bash
# After starting services
docker-compose exec backend python seed_data.py

# Creates:
# - 1 Project: "Offshore Oil Platform"
# - 1 Phase: "Exploration Phase"
# - 1 Facility: "Production Platform A"
# - 2 Wells: "Well A-01", "Well A-02"
# - 2 Subsystems: "Pump System", "Separator System"
# - 2 Persons: "John Smith" (Engineer), "Jane Doe" (Manager)
# - 1 Contractor: "TechCorp Solutions"
# - 5 Lexicon entries: BOP, ESP, 3-Phase Sep, SCADA, ROV
```

## Development Guide

### Adding a New API Endpoint

1. **Add to models.py** if needed
2. **Add to schemas.py** for request/response
3. **Add route to main.py**:
```python
@app.post("/my-endpoint")
async def my_endpoint(request: MySchema, db: Session = Depends(get_db)):
    # Your logic
    return MyResponseSchema(...)
```
4. **Test with curl or Swagger UI** at http://localhost:8000/docs

### Adding a New Celery Task

1. **Define in celery_app.py**:
```python
@celery_app.task(bind=True, max_retries=3)
def my_task(self, param1: str):
    try:
        # Your async logic
        pass
    except Exception as e:
        self.retry(exc=e, countdown=60)
```
2. **Trigger from endpoint**:
```python
my_task.delay(param1_value)
```
3. **Monitor with**:
```bash
docker-compose logs worker -f
```

### Adding a UI Component

1. Create `.tsx` file in `ui/components/`
2. Use `'use client'` directive for client-side
3. Import and use in pages:
```tsx
import MyComponent from '@/components/MyComponent';

export default function MyPage() {
  return <MyComponent />;
}
```
4. **Test locally**:
```bash
cd ui
npm run dev
# Open http://localhost:3000
```

### Local Embedding Development

If you want to test embeddings locally without LM Studio:

```python
# In embeddings.py, the _mock_embedding function is used as fallback
# For development, just use that and skip the BGE-M3 installation

# To actually run BGE-M3 locally:
pip install FlagEmbedding

# Then embeddings.py will auto-detect and use it
```

## Troubleshooting

### Docker Issues

**Container fails to start:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs worker

# Rebuild containers
docker-compose down
docker-compose up --build

# Remove volumes and restart (wipes data!)
docker-compose down -v
docker-compose up
```

**Port conflicts:**
```bash
# If port 8000, 3000, 5432, etc. are in use, edit docker-compose.yml
# Change "8000:8000" to "8001:8000" for different mapping
```

### Database Issues

**Migrations fail:**
```bash
# Reset database (careful: deletes all data!)
docker-compose exec postgres dropdb -U brain_user project_brain
docker-compose exec postgres createdb -U brain_user project_brain
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python seed_data.py
```

**Foreign key errors:**
```bash
# Ensure migrations run in correct order
docker-compose exec backend python -m alembic history
docker-compose exec backend python -m alembic current
```

### Search/Embedding Issues

**Qdrant not responding:**
```bash
# Check Qdrant health
curl http://localhost:6333/health

# Access Qdrant web UI
# http://localhost:6333/dashboard
```

**Embeddings not generated:**
```bash
# Check worker logs
docker-compose logs worker -f

# Check task status
docker-compose exec backend redis-cli
> KEYS task:*
```

### MinIO Issues

**Files not uploading:**
```bash
# Check MinIO console
# http://localhost:9001 (admin/admin)

# Verify bucket exists and has correct permissions
docker-compose logs minio
```

### Frontend Issues

**API connection errors:**
```bash
# Check NEXT_PUBLIC_API_URL in docker-compose.yml ui service
# Should be http://localhost:8000 for local, or your deployed URL

# Test API from browser console
fetch('http://localhost:8000/health').then(r => r.json()).then(console.log)
```

**Build fails:**
```bash
# Clear cache and rebuild
docker-compose down
docker system prune -a
docker-compose up --build

# Or locally:
cd ui
rm -rf .next node_modules
npm install
npm run build
npm run dev
```

## Configuration

### Environment Variables

Edit `backend/.env` or set via docker-compose:

```env
# Database
DATABASE_URL=postgresql://brain_user:brain_password@postgres:5432/project_brain

# Cache & Queue
REDIS_URL=redis://redis:6379/0

# Vector DB
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=qdrant_key

# Graph DB (optional)
NEO4J_URL=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

# Object Storage
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=project-brain

# LM Studio (local inference)
LM_STUDIO_URL=http://localhost:1234

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration

Edit `ui/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Performance Tuning

### Embeddings
- **BGE-M3** uses 1024-dim vectors by default
- For larger datasets, consider:
  - Increasing Qdrant `search_params.hnsw.ef` for accuracy
  - Using quantization for memory savings
  - Batch processing chunks

### Database
- Indexes are created on common search columns
- Enable `logging` in config.py for SQL debugging
- Consider connection pooling for high-load

### Celery
- Adjust `worker_concurrency` in docker-compose.yml
- Monitor with Flower: `celery -A celery_app flower`

## Production Deployment

### Pre-Deployment Checklist

- [ ] Update `SECRET_KEY` in config.py
- [ ] Use strong credentials for all databases
- [ ] Enable HTTPS/SSL for API and UI
- [ ] Configure authentication (JWT or OAuth2)
- [ ] Set up backups for PostgreSQL
- [ ] Configure log aggregation
- [ ] Set appropriate resource limits
- [ ] Use managed services (RDS, S3, etc.) if possible

### Example Kubernetes Deployment

See `k8s/` directory (not included in this base, but follow standard patterns)

## Testing

### Basic Tests

```bash
# Health check
curl http://localhost:8000/health

# Document upload
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@sample.pdf"

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pump failure"}'

# List documents
curl http://localhost:8000/documents
```

### Frontend Tests

```bash
cd ui
npm run build  # Check for build errors
npm run dev    # Test locally
```

## Support & Contributing

### Known Limitations

1. **Docling** requires PDF-specific handling; DOCX support via Unstructured
2. **BGE-M3** model is ~1.5GB; requires good GPU for faster inference (CPU fallback ~5s/chunk)
3. **Neo4j** is optional; graph features not fully integrated yet
4. **LM Studio** LLM inference is optional; entity linking uses keyword matching by default

### Future Roadmap

- [ ] Fine-tuned entity extraction model
- [ ] Multi-language support
- [ ] Document OCR for scanned PDFs
- [ ] Real-time collaboration
- [ ] GraphQL API
- [ ] Advanced query DSL
- [ ] Audit logging & compliance
- [ ] Custom parsing rules engine
- [ ] Batch document processing

## License

MIT License - See LICENSE file

## Contact

For issues, questions, or contributions, open a GitHub issue or contact the development team.

---

**Made with ?? for project intelligence**
