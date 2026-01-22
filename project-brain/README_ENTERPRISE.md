# Project Brain Enterprise - Intelligent Oil & Gas Project Understanding

**Project Brain** is an enterprise-grade intelligent document understanding system purpose-built for the oil & gas industry. It extracts, links, learns, and reasons about project data to enable sophisticated project management.

## What's New (Enterprise Edition)

### ?? Canonical Registry
- **Single Source of Truth**: Define all project entities (facilities, wells, subsystems, contractors, people, phases)
- **Smart Relationships**: PART_OF, OWNS, DEPENDS_ON, AFFECTS hierarchies
- **Always Consistent**: All document processing uses registry-first matching

### ?? Multi-Signal Entity Linking
- **Exact Matching**: Direct name matches
- **Fuzzy Matching**: Levenshtein distance for typos
- **Alias Recognition**: "Well-01", "W01", "WELL01" all resolve correctly
- **Context Awareness**: Embedding-based similarity
- **Smart Disambiguation**: Flags ambiguous cases for user review

### ?? Learning Rules Engine
- **Learn from Corrections**: User corrections automatically become rules
- **Persistent Rules**: Rules apply to all future documents
- **Testable Rules**: Validate rules with test cases
- **Prioritized Application**: Rules execute in priority order

### ?? Intelligent PDF Processing
- **Page Structure Parsing**: Extract text, tables, figures with bounding boxes
- **Automatic Anchoring**: Detect which object each table belongs to
- **Manual Reassignment**: Easily correct anchors with one click
- **Context Enrichment**: Chunks carry anchor information for retrieval

### ?? Object State Tracking
- **Aggregated State**: Combine all claims about an object
- **Conflict Detection**: Find competing claims automatically
- **User Resolution**: Resolve conflicts with audit trail
- **Health Scoring**: Quick dashboard of object status

### ??? Graph-Based Reasoning
- **Neo4j Integration**: Full registry sync to graph database
- **Multi-hop Search**: Find related objects up to 2 hops away
- **Contextual Retrieval**: Combine vector + graph search
- **Visual Navigation**: Explore entity relationships

## Quick Start

```bash
# Clone and setup
cd project-brain
cp .env.example .env

# Start services
docker-compose up -d

# Migrate database
docker exec project-brain-backend alembic upgrade head

# Seed demo data (oil & gas project)
docker exec project-brain-backend python seed_data.py

# Access
Backend: http://localhost:8000/docs
UI: http://localhost:3000
```

## Core Workflows

### 1?? Build Your Project Model

Define your project structure in the Registry:

```bash
# Create facility
curl -X POST http://localhost:8000/registry/entities \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "norflex_project",
    "canonical_name": "Norflex Platform A",
    "type": "facility",
    "aliases": ["NFA", "Platform-A"],
    "entity_key": "norflex_a"
  }'

# Link wells to facility
curl -X POST http://localhost:8000/registry/relations \
  -H "Content-Type: application/json" \
  -d '{
    "from_entity_id": "well-id",
    "to_entity_id": "facility-id",
    "relation_type": "PART_OF"
  }'
```

**UI**: Registry tab ? Add entities ? Create relationships

### 2?? Upload Documents

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@report.pdf" \
  -F "project_key=norflex_project"
```

**UI**: Documents tab ? Drag & drop PDF

### 3?? Fix Incorrect Table Attachment

Table should belong to "Well-03" but system anchored it to "Well-01"?

```bash
curl -X PUT http://localhost:8000/page-anchors/table-attachments/{attachment_id}/reassign \
  -H "Content-Type: application/json" \
  -d '{
    "registry_entity_id": "well-03-id",
    "user_id": "john@company.com"
  }'
```

**Result**: System learns and automatically fixes similar cases

**UI**: Document viewer ? Right-click table ? Reassign to ? Well-03

### 4?? Review Auto-Corrected Transcript

Transcript had "ÊÈÏ" (instrumentation) misspelled?

```bash
GET http://localhost:8000/transcripts/{doc_id}/corrections
```

**UI**: Transcript tab ? Review corrections ? Approve/Reject

**Result**: Each approval creates a normalization rule

### 5?? View Status Report

Get comprehensive status for an object:

```bash
curl -X POST http://localhost:8000/state/report/{entity_id} \
  -H "Content-Type: application/json" \
  -d '{"as_of_date": "2024-01-15"}'
```

Response includes:
- **Aggregated State**: Latest values from all sources
- **Conflicts**: Competing claims (e.g., 80% vs 85% completion)
- **Health Score**: Quick status at a glance
- **Evidence**: Links to source documents

**UI**: Status tab ? Select object ? View detailed report

### 6?? Resolve State Conflicts

User confirms progress is 85%, not 80%:

```bash
curl -X POST http://localhost:8000/state/conflicts/{entity_id}/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "field_path": "progress_percent",
    "chosen_value": 85,
    "reason": "Latest progress report confirms 85%"
  }'
```

**Result**: All future state computations use 85%

**UI**: Status ? Conflicts section ? Choose value ? Resolve

### 7?? Query with Context

What's blocking Facility A?

```bash
curl -X POST http://localhost:8000/assist/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What issues affect Facility A?",
    "scope_entities": ["facility-a-id"],
    "mode": "graph_rag"
  }'
```

System will:
1. Identify "Facility A" in registry
2. Find subsystems and wells (PART_OF)
3. Find all issues on those subsystems
4. Return issues + evidence + reasoning

## Architecture

```
???????????????????????????????????????????
?         User Interface (Next.js)        ?
?  Registry | Rules | Status | Documents ?
???????????????????????????????????????????
                     ?
????????????????????????????????????????????
?        FastAPI Backend                  ?
? /registry /page-anchors /state /rules   ?
????????????????????????????????????????????
       ?              ?              ?
   ????????      ???????????    ??????????
   ?Vector?      ?PostgreSQL      ?Neo4j  ?
   ?Search?      ? Registry ?      ?Graph  ?
   ?Qdrant?      ? State    ?      ?       ?
   ????????      ????????????      ?????????
```

### Components

| Component | Role |
|-----------|------|
| **Registry** | Canonical entity database with relationships |
| **Entity Linker v2** | Multi-signal mention resolution |
| **Rules Engine** | Learn from corrections, auto-apply |
| **Page Anchoring** | Link tables to objects |
| **State Aggregator** | Merge claims, detect conflicts |
| **GraphRAG** | Context-aware retrieval |

## Data Flows

### Correction ? Rule Learning

```
User reassigns table
     ?
Curation event created
     ?
RulesEngine.create_rule_from_event()
     ?
Rule stored with priority
     ?
Next document ? Rule applies automatically
     ?
Auto-correction with full traceability
```

### PDF Upload ? Smart Anchoring

```
Upload PDF
     ?
Parse to blocks (text, tables, figures)
     ?
Detect object references (regex + fuzzy match vs registry)
     ?
Attach tables to nearest anchor
     ?
User can reassign if incorrect
     ?
Chunks include anchor info for retrieval
```

### Query ? Graph Search

```
User query
     ?
Link query mentions to registry entities
     ?
Expand via relationships (1-2 hops)
     ?
Combine with vector search on subgraph
     ?
Ranked results with explanation
     ?
Show related entities + sources
```

## Key Features

### Registry Management
- ? Create/edit/delete entities
- ? Manage aliases (synonyms, abbreviations)
- ? Define relationships (PART_OF, OWNS, DEPENDS_ON)
- ? Hierarchical tree view
- ? Bulk import (CSV/JSON)
- ? Entity merge/deduplication

### Entity Linking
- ? Exact match (canonical names)
- ? Alias match (abbreviations, synonyms)
- ? Fuzzy match (typo tolerance)
- ? Embedding-based similarity
- ? Contextual boost
- ? Ambiguity detection ? pending review

### Rules Engine
- ? Link fix rules
- ? Lexicon normalization rules
- ? Claim override rules
- ? Parsing anchor rules
- ? Priority-based execution
- ? Test case validation

### PDF Processing
- ? Structure extraction (blocks with bbox)
- ? Table detection
- ? Automatic anchoring to entities
- ? Manual reassignment
- ? Learning from corrections

### State Management
- ? Aggregate claims about objects
- ? Detect competing claims
- ? Conflict resolution UI
- ? Health scoring
- ? Timeline of changes

### Retrieval & Reporting
- ? Vector search with anchor bias
- ? Graph-based relationship traversal
- ? Combined GraphRAG retrieval
- ? Status reports with evidence
- ? Conflict summaries
- ? Audit trails

## Configuration

See `.env.example` and `OPERATIONS_GUIDE.md` for all options.

Key thresholds:
- `AUTO_LINK_THRESHOLD=0.75` - Auto-link if score > threshold
- `PENDING_REVIEW_THRESHOLD=0.6` - Flag for review if below
- `CORRECTION_APPLY_THRESHOLD=0.8` - Apply corrections if confident

## API Reference

### Registry Endpoints

```
POST   /registry/entities              Create entity
GET    /registry/entities              List entities (with filters)
GET    /registry/entities/{id}         Get entity details
PUT    /registry/entities/{id}         Update entity
DELETE /registry/entities/{id}         Archive entity

POST   /registry/relations             Create relationship
GET    /registry/relations             List relationships
DELETE /registry/relations/{id}        Delete relationship

POST   /registry/merge                 Merge duplicate entities
POST   /registry/import                Bulk import
GET    /registry/tree                  Hierarchical view
POST   /registry/link-mention          Link text mention
```

### Page Anchoring

```
POST   /page-anchors/detect            Detect anchors on page
PUT    /page-anchors/table-attachments/{id}/reassign  Reassign table
GET    /page-anchors/table-attachments/{doc}         List attachments
```

### State & Conflicts

```
POST   /state/compute                  Compute object state
GET    /state/entity/{id}              Get latest state
GET    /state/conflicts/{id}           List conflicts
POST   /state/conflicts/{id}/resolve   Resolve conflict
POST   /state/report/{id}              Generate status report
```

### Rules

```
POST   /rules/create-from-event        Create rule from event
GET    /rules/                         List rules
GET    /rules/{id}                     Get rule details
PUT    /rules/{id}                     Update rule
POST   /rules/{id}/test                Test rule
DELETE /rules/{id}                     Delete rule
```

Full API: http://localhost:8000/docs

## Troubleshooting

### Entity linking returns low scores?
? Check registry has entities + aliases  
? Verify mention matches expected names  
? Lower confidence threshold for testing  

### Tables not anchoring correctly?
? Ensure registry has complete entity names  
? Manually reassign (system learns)  
? Check page text for anchor patterns  

### Rules not applying?
? Verify rule enabled: `GET /rules/{id}`  
? Check rule priority  
? Test rule: `POST /rules/{id}/test`  

### Status conflicts won't resolve?
? Verify conflict exists: `GET /state/conflicts/{id}`  
? Try manually picking value  
? Check resolution event was created  

**More help**: See `OPERATIONS_GUIDE.md` or `ARCHITECTURE_ENHANCED.md`

## Technology Stack

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **Celery** - Task queue
- **Redis** - Cache

### Databases
- **PostgreSQL** - Relational data (documents, entities, state)
- **Qdrant** - Vector search (embeddings)
- **Neo4j** - Graph database (relationships)

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **SWR** - Data fetching

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **MinIO** - S3-compatible storage

## License

[Your License Here]

## Contributing

PRs welcome! See repository for contribution guidelines.

## Support

- **Documentation**: See ARCHITECTURE_ENHANCED.md, OPERATIONS_GUIDE.md
- **Issues**: Open GitHub issue with logs from `/debug/run/{correlation_id}`
- **Community**: [Your community platform]

---

**Made for oil & gas project teams who need to understand their projects deeply.**
