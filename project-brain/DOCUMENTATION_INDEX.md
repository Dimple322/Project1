# Project Brain - Documentation Index

## ?? Documentation Files

### Getting Started
1. **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** ? **START HERE**
   - Complete overview of what's included
   - Quick start instructions
   - Key features and architecture highlights
   - File structure and technology stack

2. **[README.md](./README.md)**
   - Detailed setup instructions
   - Full API documentation (43 endpoints)
   - Project structure explanation
   - Development guide and troubleshooting
   - Docker Compose configuration

3. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - DB-first design principles
   - Detailed data flow diagrams
   - Database schema explanation
   - API architecture
   - Async task processing
   - Search & embedding pipeline
   - Performance tuning tips

### Quick Reference

#### For New Users
1. Read: `IMPLEMENTATION_SUMMARY.md` (5 min)
2. Run: `./quick-start.sh` or `quick-start.bat` (5 min)
3. Explore: http://localhost:3000 (frontend) and http://localhost:8000/docs (API)

#### For Backend Developers
1. Review: `backend/main.py` (routes)
2. Review: `backend/models.py` (database schema)
3. Review: `backend/schemas.py` (API request/response)
4. Review: `backend/celery_app.py` (async tasks)
5. Reference: `ARCHITECTURE.md` (data flow)

#### For Frontend Developers
1. Review: `ui/app/page.tsx` (home page)
2. Review: `ui/lib/api.ts` (API client)
3. Review: `ui/components/` (reusable components)
4. Reference: `README.md` (API endpoints)

#### For DevOps/Deployment
1. Review: `docker-compose.yml` (full stack)
2. Review: `Dockerfile` files (containerization)
3. Review: `.env.example` (configuration)
4. Reference: `README.md` (deployment section)

## ??? Project Structure

```
project-brain/
??? IMPLEMENTATION_SUMMARY.md    ? Complete overview (START HERE)
??? README.md                    ? Detailed guide + API docs
??? ARCHITECTURE.md              ? Technical deep-dive
??? DOCUMENTATION_INDEX.md       ? This file
??? Makefile                     ? Development commands
??? docker-compose.yml           ? Full stack definition
??? .env.example                 ? Configuration template
??? quick-start.sh              ? Linux/Mac setup
??? quick-start.bat             ? Windows setup
?
??? backend/                     ? Python FastAPI Backend
?   ??? main.py                 ? 43 API routes
?   ??? models.py               ? 17 database tables
?   ??? schemas.py              ? Request/response validation
?   ??? db.py                   ? Database connection
?   ??? config.py               ? Settings & environment
?   ??? logger.py               ? Logging configuration
?   ??? storage.py              ? MinIO file client
?   ??? parsing.py              ? Document parsing (Docling + Unstructured)
?   ??? embeddings.py           ? BGE-M3 embeddings + BGE-Reranker ranking
?   ??? transcript_corrector.py ? Lexicon-based correction
?   ??? meeting_extractor.py    ? Extract issues/actions/decisions
?   ??? celery_app.py           ? 4 async tasks (parse, embed, correct, extract)
?   ??? seed_data.py            ? Demo data with 7 entities
?   ??? requirements.txt         ? Python dependencies
?   ??? Dockerfile              ? Backend container
?   ??? alembic.ini             ? Migration config
?   ??? .env                     ? Environment file
?   ??? alembic/
?       ??? env.py              ? Alembic environment
?       ??? versions/
?           ??? 001_initial_schema.py ? Database schema
?
??? ui/                          ? Next.js React Frontend
    ??? app/                     ? Next.js App Router
    ?   ??? page.tsx            ? Home page
    ?   ??? layout.tsx          ? Root layout
    ?   ??? globals.css         ? Global styles
    ?   ??? documents/          ? Documents page
    ?   ??? search/             ? Search page
    ?   ??? pending-review/     ? Pending review page
    ?   ??? reports/            ? Status reports page
    ?   ??? entities/           ? Entity management (template)
    ??? components/              ? Reusable React components
    ?   ??? Navbar.tsx
    ?   ??? DocumentUpload.tsx
    ?   ??? DocumentList.tsx
    ?   ??? SearchComponent.tsx
    ??? lib/                     ? Utilities
    ?   ??? api.ts              ? Axios client + API endpoints
    ?   ??? hooks.ts            ? Custom React hooks
    ??? package.json            ? Node dependencies
    ??? tsconfig.json           ? TypeScript config
    ??? tailwind.config.js      ? Tailwind CSS config
    ??? next.config.js          ? Next.js config
    ??? Dockerfile              ? UI container
```

## ?? Common Tasks

### Starting Development
```bash
# Automatic setup
cd project-brain
./quick-start.sh  # Linux/Mac
# or
quick-start.bat   # Windows

# Or manual setup
docker-compose up -d
docker-compose exec backend python -m alembic upgrade head
docker-compose exec backend python seed_data.py
```

### Adding a New API Endpoint
1. **Add database model** in `backend/models.py`
2. **Add Pydantic schema** in `backend/schemas.py`
3. **Add route** in `backend/main.py`
4. **Test** at http://localhost:8000/docs

### Adding a New Frontend Page
1. **Create file** `ui/app/my-feature/page.tsx`
2. **Add navigation** link in `ui/components/Navbar.tsx`
3. **Use API client** from `ui/lib/api.ts`
4. **Test** at http://localhost:3000/my-feature

### Adding a New Async Task
1. **Define task** in `backend/celery_app.py` with `@celery_app.task`
2. **Trigger** from endpoint: `my_task.delay(params)`
3. **Monitor** via `docker-compose logs worker -f`

### Running Database Migrations
```bash
# Create new migration
docker-compose exec backend python -m alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend python -m alembic upgrade head

# Rollback last migration
docker-compose exec backend python -m alembic downgrade -1
```

### Viewing Logs
```bash
docker-compose logs -f backend   # Backend API logs
docker-compose logs -f worker    # Celery worker logs
docker-compose logs -f ui        # Frontend logs
docker-compose logs -f postgres  # Database logs
```

### Testing API
```bash
# Health check
curl http://localhost:8000/health

# List documents
curl http://localhost:8000/documents

# Search documents
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pump", "limit": 10}'

# Interactive API docs
open http://localhost:8000/docs
```

## ?? Database Schema Overview

### Documents & Content
- `documents` - Original uploaded files (SHA256 hash for idempotency)
- `document_versions` - Multiple versions with parsing status
- `chunks` - Parsed text segments with page/section info
- `lexicon` - Terms, abbreviations, synonyms for correction

### Extraction Results
- `issues` - Problems/concerns extracted from documents
- `action_items` - Tasks extracted from meetings
- `decisions` - Decisions extracted from documents
- `claims` - Subject-specific statements with evidence

### Entity Registry
- `projects` - Top-level projects
- `phases` - Project phases
- `facilities` - Physical facilities
- `wells` - Wells within facilities
- `subsystems` - Equipment/systems within facilities
- `contractors` - Service providers
- `persons` - Individuals
- `entity_mentions` - Links between chunks and entities

### Support Tables
- `transcript_corrections` - Corrected transcripts with diffs
- `curation_events` - Audit trail of manual edits
- `tasks` - Background job queue and status
- `claims` - Subject-specific claims with evidence

## ?? Configuration Files

### `.env` (Environment Variables)
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
QDRANT_URL=http://...
MINIO_URL=http://...
LM_STUDIO_URL=http://...  # Optional
LOG_LEVEL=INFO
```

### `docker-compose.yml` (Container Orchestration)
- PostgreSQL 15
- Redis 7
- Qdrant (vectors)
- Neo4j 5 (graph, optional)
- MinIO (object storage)
- FastAPI backend
- Celery worker
- Next.js frontend

### `Makefile` (Development Commands)
```bash
make up              # Start all services
make down            # Stop all services
make logs            # Show all logs
make migrate         # Run database migrations
make seed            # Seed demo data
make test-api        # Test API health
```

## ?? Key Concepts

### DB-First Architecture
- PostgreSQL is the single source of truth
- Specialized stores (Qdrant, Neo4j, MinIO) support specific features
- All data originates from and is reconciled with the relational DB

### Idempotency
- SHA256 hashing prevents duplicate documents
- Version numbering allows re-processing
- Task IDs enable safe retries

### Async Processing
- Long-running operations (parse, embed) run async via Celery
- Redis queues tasks, stores cache
- Auto-retries with exponential backoff

### Search & Ranking
```
Query ? BGE-M3 (embed) ? Qdrant (semantic search) ? BGE-Reranker (rank)
```

### Evidence & Confidence
- Every extracted item links to source (chunk_id + quote)
- Confidence scores enable review filtering
- Pending review system for human approval

### Curation Trail
- Every edit is recorded (LINK_FIX, ENTITY_MERGE, etc.)
- Immutable audit log
- Applied in subsequent processing runs

## ?? Links

- **Interactive API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **MinIO Console**: http://localhost:9001
- **Neo4j Browser**: http://localhost:7474

## ?? Reading Order (Recommended)

1. **For non-technical users**:
   - IMPLEMENTATION_SUMMARY.md (5 min)
   - README.md ? Quick Start section (5 min)
   - Try uploading documents at http://localhost:3000

2. **For developers**:
   - IMPLEMENTATION_SUMMARY.md (5 min)
   - README.md ? Project Structure (10 min)
   - backend/main.py ? Skim routes (10 min)
   - backend/models.py ? Review schema (10 min)
   - ARCHITECTURE.md ? Read sections relevant to your work

3. **For architects/leads**:
   - IMPLEMENTATION_SUMMARY.md (10 min)
   - ARCHITECTURE.md ? Full read (30 min)
   - Diagram: `System Design` section (5 min)
   - Database schema overview (10 min)

## ?? Troubleshooting

See the **Troubleshooting** section in `README.md` for:
- Docker issues
- Database issues
- Search/embedding issues
- MinIO issues
- Frontend issues

## ?? Files Summary

| File | Type | Purpose | Lines |
|------|------|---------|-------|
| main.py | Code | FastAPI routes | 500+ |
| models.py | Code | Database schema | 400+ |
| celery_app.py | Code | Async tasks | 350+ |
| parsing.py | Code | Document parsing | 150+ |
| embeddings.py | Code | Embeddings + reranking | 100+ |
| README.md | Docs | Getting started guide | 600+ |
| ARCHITECTURE.md | Docs | Technical documentation | 500+ |
| IMPLEMENTATION_SUMMARY.md | Docs | Overview | 300+ |
| docker-compose.yml | Config | Container setup | 150+ |
| requirements.txt | Config | Python dependencies | 25 packages |
| | | **Total** | **5000+ lines** |

---

**Last Updated**: 2024-01-15  
**Status**: ? Production-Ready  
**Ready to Deploy**: Yes
