# Project Brain Enterprise - Deployment & Operations Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 13+
- Redis 6+
- Qdrant
- Neo4j

### Setup

```bash
# 1. Clone and navigate
cd project-brain

# 2. Copy environment template
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker exec project-brain-backend alembic upgrade head

# 5. Seed database with demo data
docker exec project-brain-backend python seed_data.py

# 6. Access UI
open http://localhost:3000
```

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://brain_user:brain_password@postgres:5432/project_brain

# API
API_TITLE=Project Brain
API_VERSION=v1.0.0
API_HOST=0.0.0.0
API_PORT=8000

# Redis (Celery)
REDIS_URL=redis://redis:6379/0

# Qdrant (Vector Search)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=

# Neo4j (Graph Database)
NEO4J_URI=neo4j://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# MinIO (S3 Storage)
MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_USE_SSL=False
MINIO_BUCKET_NAME=project-brain

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Thresholds
AUTO_LINK_THRESHOLD=0.75
PENDING_REVIEW_THRESHOLD=0.6
CORRECTION_APPLY_THRESHOLD=0.8
ENTITY_TYPE_HINT_BOOST=0.1
```

## Operations

### Registry Management

#### 1. Populate Registry with Entities

```bash
# Option A: Via API
curl -X POST http://localhost:8000/registry/import \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "norflex_project",
    "entities": [
      {
        "canonical_name": "Facility A",
        "type": "facility",
        "aliases": ["FA", "Facility-A"],
        "entity_key": "facility_a"
      }
    ]
  }'

# Option B: Direct SQL
psql -h localhost -U brain_user -d project_brain < seed_registry.sql
```

#### 2. Create Relationships

```bash
curl -X POST http://localhost:8000/registry/relations \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "norflex_project",
    "from_entity_id": "well-id",
    "to_entity_id": "facility-id",
    "relation_type": "PART_OF"
  }'
```

#### 3. Merge Duplicate Entities

```bash
curl -X POST http://localhost:8000/registry/merge \
  -H "Content-Type: application/json" \
  -d '{
    "from_entity_id": "duplicate-id",
    "to_entity_id": "canonical-id",
    "reason": "duplicate facility"
  }'
```

### Document Processing

#### 1. Upload Document

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@/path/to/report.pdf"
```

#### 2. Check Processing Status

```bash
curl http://localhost:8000/documents/{doc_id}
```

#### 3. View Document Chunks

```bash
curl http://localhost:8000/documents/{doc_id}/chunks
```

### PDF Table Attachment

#### 1. Automatic Table Detection

After document parsing, tables are automatically detected and anchored:

```bash
curl http://localhost:8000/page-anchors/page/{doc_version_id}/{page_number}
```

#### 2. Manual Table Reassignment

```bash
curl -X PUT http://localhost:8000/page-anchors/table-attachments/{attachment_id}/reassign \
  -H "Content-Type: application/json" \
  -d '{
    "registry_entity_id": "correct-entity-id",
    "user_id": "john.smith@company.com"
  }'
```

This creates a curation event that triggers rule learning.

### Entity Linking

#### 1. Link a Mention

```bash
curl -X POST http://localhost:8000/registry/link-mention \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "norflex_project",
    "mention_text": "Well-01",
    "context": "Production from Well-01 reached 1000 bbl/day",
    "confidence_threshold": 0.75
  }'
```

Response:
```json
{
  "mention": "Well-01",
  "candidates": [
    {
      "entity_id": "well-01-id",
      "name": "Well-01",
      "score": 0.99,
      "signals": ["exact_match", "alias_match"],
      "reasons": ["Exact match: 'Well-01' == 'Well-01'"]
    }
  ],
  "best_match": {
    "entity_id": "well-01-id",
    "name": "Well-01",
    "score": 0.99
  },
  "is_ambiguous": false
}
```

#### 2. Link Ambiguous Mention

If `is_ambiguous: true`, the system creates a pending review item instead of auto-linking.

### Rules Engine

#### 1. View Learned Rules

```bash
curl http://localhost:8000/rules/?rule_type=LINK_FIX_RULE&enabled=true
```

#### 2. Disable a Rule

```bash
curl -X PUT http://localhost:8000/rules/{rule_id} \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

#### 3. Test a Rule

```bash
curl -X POST http://localhost:8000/rules/{rule_id}/test \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "norflex_project",
    "test_input": {
      "mention": "Well-01",
      "context": "Production data"
    }
  }'
```

#### 4. Add Test Case to Rule

```bash
curl -X POST http://localhost:8000/rules/{rule_id}/test-cases/add \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"mention": "Well-01"},
    "expected_output": {"entity_id": "well-01-id"},
    "description": "Link Well-01 to correct facility"
  }'
```

### State Management

#### 1. Compute Object State

```bash
curl -X POST http://localhost:8000/state/compute \
  -H "Content-Type: application/json" \
  -d '{
    "registry_entity_id": "facility-id",
    "as_of_date": "2024-01-15"
  }'
```

#### 2. Get Object State

```bash
curl http://localhost:8000/state/entity/{entity_id}?as_of_date=2024-01-15
```

#### 3. View Conflicts

```bash
curl http://localhost:8000/state/conflicts/{entity_id}?status=open
```

#### 4. Resolve Conflict

```bash
curl -X POST http://localhost:8000/state/conflicts/{entity_id}/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "field_path": "progress_percent",
    "chosen_value": 85,
    "reason": "Latest progress report confirms 85%",
    "user_id": "maria.garcia@company.com"
  }'
```

#### 5. Generate Status Report

```bash
curl -X POST http://localhost:8000/state/report/{entity_id} \
  -H "Content-Type: application/json" \
  -d '{
    "as_of_date": "2024-01-15"
  }'
```

Response includes:
- Entity details
- Current state (aggregated from claims)
- Open conflicts
- Health score (0-1)
- Summary statistics

### Curation Events & Learning

#### 1. Create Curation Event

```bash
curl -X POST http://localhost:8000/curation/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "LINK_FIX",
    "object_id": "mention-id",
    "object_type": "entity_mention",
    "metadata": {
      "mention_text": "W01",
      "entity_id": "well-01-id",
      "context": "Production data"
    }
  }'
```

#### 2. Create Rule from Event

```bash
curl -X POST http://localhost:8000/rules/create-from-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "curation-event-id",
    "project_key": "norflex_project"
  }'
```

### Monitoring & Debugging

#### 1. View Run Trace

```bash
curl http://localhost:8000/debug/run/{correlation_id}
```

Returns:
- Pipeline stages
- Entity linking decisions with scores
- Rule applications
- State computation steps

#### 2. Check Task Status

```bash
curl http://localhost:8000/tasks/{task_id}
```

#### 3. View Logs

```bash
# Docker logs
docker logs -f project-brain-backend

# Or query database
psql -h localhost -U brain_user -d project_brain \
  -c "SELECT * FROM logs WHERE correlation_id = '{id}' ORDER BY created_at"
```

## Maintenance

### Database

#### Backup
```bash
docker exec postgres pg_dump -U brain_user project_brain > backup_$(date +%Y%m%d).sql
```

#### Restore
```bash
docker exec postgres psql -U brain_user project_brain < backup_20240115.sql
```

#### Vacuum & Analyze
```bash
psql -h localhost -U brain_user -d project_brain -c "VACUUM ANALYZE"
```

### Migrations

#### Create New Migration
```bash
docker exec project-brain-backend alembic revision --autogenerate -m "description"
```

#### Apply Migrations
```bash
docker exec project-brain-backend alembic upgrade head
```

#### Rollback
```bash
docker exec project-brain-backend alembic downgrade -1
```

### Vector Database

#### Reindex
```bash
curl -X POST http://localhost:6333/collections/chunks/points/clear
```

#### Backup
```bash
curl http://localhost:6333/collections/chunks > qdrant_backup.json
```

### Graph Database

#### Backup Neo4j
```bash
docker exec neo4j neo4j-admin dump --to-path=/data/backup --database=neo4j
```

## Troubleshooting

### Issue: "Entity linking returns low scores"

**Diagnosis:**
1. Check if registry populated: `curl http://localhost:8000/registry/entities?project_key=norflex_project`
2. Verify aliases: Look at top candidate's `reasons` field
3. Check context: Provide more surrounding text

**Solution:**
1. Add missing aliases to registry entities
2. Lower confidence_threshold temporarily for testing
3. Create LINK_FIX_RULE for common patterns

### Issue: "Tables not attached to entities"

**Diagnosis:**
1. Check if anchors detected: `curl http://localhost:8000/page-anchors/page/{doc_id}/{page}`
2. Verify entity names match patterns in registry

**Solution:**
1. Ensure registry entities have complete aliases
2. Manually reassign with `/page-anchors/table-attachments/{id}/reassign`
3. System learns from corrections automatically

### Issue: "State conflicts not resolved"

**Diagnosis:**
1. Check conflicts: `curl http://localhost:8000/state/conflicts/{entity_id}`
2. View competing claims in state computation

**Solution:**
1. Manually choose correct value via resolve endpoint
2. Verify CLAIM_OVERRIDE_RULE was created
3. Rule will apply to future state computations

### Issue: "Rules not applying to new documents"

**Diagnosis:**
1. Check rule enabled: `curl http://localhost:8000/rules/{rule_id}`
2. Verify rule priority
3. Test rule: `POST /rules/{rule_id}/test`

**Solution:**
1. Enable rule if disabled
2. Increase priority if needed
3. Add test cases to rule
4. Check rule payload for correctness

## Performance Tuning

### Database
```sql
-- Add index for common queries
CREATE INDEX idx_curation_events_project ON curation_events(project_key, created_at DESC);
CREATE INDEX idx_chunks_anchor ON chunks(anchor_entity_id, doc_version_id);

-- Monitor slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second
SELECT reload_conf();
```

### Qdrant
- Increase `hnsw_config.ef_construct` for better recall
- Use MMAP storage for large collections
- Enable quantization for reduced memory

### Neo4j
- Increase heap size: `-Xmx8g`
- Enable query cache
- Create indexes on frequently filtered properties

### API
- Cache registry in memory per project
- Use connection pooling for database
- Batch entity linking requests

## Scaling Recommendations

### For 10+ simultaneous users
- 2x API instances behind load balancer
- 3x parse_worker, 2x embed_worker
- PostgreSQL with read replicas
- Redis cluster for caching

### For 100+ simultaneous users
- Kubernetes deployment
- PostgreSQL sharding by project_key
- Qdrant cluster
- Neo4j cluster
- Horizontal autoscaling

## Security Checklist

- [ ] Change default passwords in .env
- [ ] Enable PostgreSQL SSL connection
- [ ] Use TLS for MinIO
- [ ] Restrict API to internal network initially
- [ ] Enable authentication on Neo4j
- [ ] Audit curation events regularly
- [ ] Backup database daily
- [ ] Monitor failed linking attempts for anomalies

## Support & Documentation

- **Issues**: Check logs with `docker logs project-brain-backend`
- **Debugging**: Use `/debug/run/{correlation_id}` endpoint
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Architecture**: See ARCHITECTURE_ENHANCED.md
- **Contributing**: Follow patterns in existing code
