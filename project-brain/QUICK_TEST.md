# Quick Test Guide for Project Brain

## Prerequisites
- Docker & Docker Compose installed
- LM Studio running on http://10.146.65.224:1234
- Mistral 3.14B model loaded in LM Studio

## 5-Minute Setup & Test

### Step 1: Start Services (30s)
```bash
cd project-brain
docker compose down
docker compose up -d --build
echo "Waiting for services to start..."
sleep 60
```

### Step 2: Verify Services (1m)
```bash
# Check all containers are running
docker compose ps

# Should see: backend, worker, postgres, redis, qdrant, neo4j, minio, ui
```

### Step 3: Create Test Document (30s)

Create a test file `test.txt`:
```
SAFETY OPERATIONS MANUAL

Chapter 1: Equipment Safety
All personnel must wear safety helmets and protective gear at all times.
Emergency procedures must be reviewed monthly.

Chapter 2: Incident Reporting
Report all incidents within 24 hours to the safety officer.
Include details: time, location, people involved, and damage assessment.

Chapter 3: Chemical Handling
Only trained personnel can handle chemicals.
All chemicals must be stored in designated containers.
SDS (Safety Data Sheets) must be available for all chemicals.
```

### Step 4: Upload Document (1m)

**Option A: Via UI**
```
1. Open http://localhost:3000
2. Click "Upload Document"
3. Select test.txt
4. Click Upload
5. Wait for "Ingested successfully"
```

**Option B: Via curl**
```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@test.txt" \
  -F "credentials=include"

# Should return: {"status": "ingested", "document_id": "..."}
```

### Step 5: Test Search (1m)

**Option A: Via UI**
```
1. Go to http://localhost:3000/search
2. Click "Search Documents" tab
3. Search: "safety helmet"
4. Should see result with relevance score
```

**Option B: Via curl**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "safety helmet",
    "limit": 5,
    "offset": 0
  }'

# Expected response:
# {
#   "results": [
#     {
#       "text": "All personnel must wear safety helmets...",
#       "score": 0.92,
#       "document_id": "...",
#       "chunk_id": "..."
#     }
#   ],
#   "total": 1
# }
```

### Step 6: Test Ask (RAG) (1m)

**Option A: Via UI**
```
1. Go to http://localhost:3000/search
2. Click "Ask with RAG" tab
3. Ask: "What are the safety requirements?"
4. Wait for LLM response (~5-10 seconds)
5. See answer + sources
```

**Option B: Via curl**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the safety requirements?",
    "max_context_chunks": 3
  }'

# Expected response:
# {
#   "answer": "Based on the documents, safety requirements include...",
#   "sources": [
#     {
#       "filename": "test.txt",
#       "doc_id": "...",
#       "score": 0.95
#     }
#   ],
#   "context_chunks": 3,
#   "status": "success"
# }
```

### Step 7: Test Knowledge Graph (1m)

**Option A: Via UI**
```
1. Go to http://localhost:3000/graph
2. See graph visualization
3. Should show nodes (document, chunks)
4. Click "View All Nodes" to see details
```

**Option B: Via curl**
```bash
curl http://localhost:8000/graph

# Expected response:
# {
#   "nodes": [
#     {
#       "id": "doc_id",
#       "label": "test.txt",
#       "type": "document"
#     },
#     {
#       "id": "chunk_id",
#       "label": "All personnel must wear...",
#       "type": "chunk"
#     }
#   ],
#   "edges": [
#     {
#       "source": "doc_id",
#       "target": "chunk_id",
#       "type": "contains"
#     }
#   ],
#   "total_nodes": 2,
#   "total_edges": 1
# }
```

## ? Success Checklist

- [ ] All containers running (`docker compose ps`)
- [ ] Document uploaded successfully
- [ ] Search returns results with scores
- [ ] Ask returns LLM answer + sources
- [ ] Graph shows nodes and edges
- [ ] UI pages load: /documents, /search, /graph

## ?? Common Issues & Fixes

### Issue: "LLM not available"
**Solution:**
```bash
# Check LM Studio status
curl http://10.146.65.224:1234/v1/models

# Restart LM Studio if needed
# Ask endpoint will gracefully fall back to search-only
```

### Issue: Search returns empty
**Solution:**
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Check embedding service logs
docker compose logs backend | grep -i embed
```

### Issue: Graph shows "Limited"
**Solution:**
```bash
# Neo4j may not be configured - this is OK
# Graph still shows document structure
# Neo4j is optional for MVP

# If you want to fix it:
docker compose logs neo4j
```

### Issue: "Connection refused" on localhost:3000
**Solution:**
```bash
# Wait for UI to build (first time ~60s)
docker compose logs ui | tail -20

# If still failing:
docker compose restart ui
```

## ?? Performance Notes

- First search: ~2-5s (embedding generation)
- Subsequent searches: <1s (cached embeddings)
- Ask (RAG): 5-15s (includes LLM inference)
- Graph: ~1s

## ?? What Just Happened?

1. **Document Upload**: File ? chunks ? embeddings ? Qdrant
2. **Search**: Query ? embedding ? vector search in Qdrant ? ranked results
3. **Ask (RAG)**: Query ? search results ? context ? LLM ? answer
4. **Graph**: Retrieved document/chunk nodes from Neo4j or in-memory model

This is a complete AI/ML pipeline! ??

## ?? Next Steps

- [ ] Try different queries
- [ ] Upload multiple documents
- [ ] Test with PDFs (automatic parsing)
- [ ] Check logs: `docker compose logs -f backend`
- [ ] Read FIXES_SUMMARY.md for architecture details
