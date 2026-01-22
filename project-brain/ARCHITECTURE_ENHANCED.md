# Project Brain Enterprise Architecture

## System Overview

Project Brain is an intelligent document understanding system designed for the oil & gas industry, enabling sophisticated project management through:

- **Canonical Registry**: Single source of truth for project entities
- **Smart Entity Linking**: Disambiguation with multiple scoring signals
- **Learning Rules Engine**: System learns from user corrections
- **PDF Anchoring**: Intelligent table attachment to project objects
- **State Aggregation**: Current status tracking with conflict detection
- **GraphRAG**: Graph-based retrieval for contextual reasoning

## Architecture Layers

### 1. Data Layer (PostgreSQL)

#### Core Tables
- `documents` - Source documents (PDFs, transcripts)
- `document_versions` - Versioned parsing results
- `chunks` - Text segments with embeddings

#### Registry Tables (NEW)
- `registry_entities` - Canonical project objects (facilities, wells, subsystems, contractors, people, phases)
- `registry_relations` - Relationships between entities (PART_OF, OWNED_BY, DEPENDS_ON, AFFECTS, RELATES_TO)
- `registry_constraints` - Rules for entity management

#### PDF Structure Tables (NEW)
- `doc_page_blocks` - Structured page elements (text, tables, figures)
- `page_anchors` - Detected object references on pages
- `table_attachments` - Link tables to entities

#### Learning Tables (NEW)
- `curation_rules` - Rules learned from user corrections
- `curation_events` - User curation actions

#### State Tables (NEW)
- `object_state` - Current state of entities (aggregated from claims)
- `state_conflicts` - Competing claims about entity state

### 2. Knowledge Layer

#### Entity Linking (linking_v2.py)
```python
EntityLinker
??? link() - Main linking function with scoring
??? _score_candidate() - Multi-signal scoring
?   ??? Exact match
?   ??? Alias match
?   ??? Fuzzy match (Levenshtein)
?   ??? Embedding similarity
?   ??? Anchor bias (PART_OF boost)
?   ??? Frequency prior
??? disambiguate() - Handle ambiguous cases
??? build_context_pack() - Project context
```

#### Rules Engine (rules_engine.py)
```python
CurationRulesEngine
??? create_rule_from_event() - Convert correction ? rule
??? apply_link_fix_rules() - Entity linking corrections
??? apply_normalization_rules() - Lexicon corrections
??? apply_claim_override_rules() - Value overrides
??? test_rule() - Rule validation

RulePipeline
??? process_mention() - Apply all mention rules
??? process_text() - Apply all text rules
```

#### Page Anchoring (page_anchoring.py)
```python
AnchorDetector
??? detect_anchors() - Find object references on pages
??? _find_block_for_position() - Locate block by text position

TableAttachmentService
??? attach_table_to_anchor() - Explicit attachment
??? auto_attach_tables() - Proximity-based attachment
??? manual_attachment() - User reassignment

PageStructureParser
??? extract_blocks_from_docling() - From Docling output
??? extract_blocks_fallback() - From existing chunks
```

#### State Model (state_model.py)
```python
StateAggregator
??? compute_state() - Build state from claims
??? _aggregate_claims() - Merge claims by field
??? _apply_overrides() - Apply override rules
??? save_state() - Persist state
??? detect_conflicts() - Find competing claims
??? resolve_conflict() - User resolution

StateReportBuilder
??? build_status_report() - Comprehensive report
??? _build_summary() - Executive summary
??? _compute_health() - Health score (0-1)
```

### 3. API Layer (FastAPI)

#### Registry Endpoints
```
POST   /registry/entities              - Create entity
GET    /registry/entities              - List with filters
GET    /registry/entities/{id}         - Get details
PUT    /registry/entities/{id}         - Update entity
DELETE /registry/entities/{id}         - Archive entity

POST   /registry/relations             - Create relation
GET    /registry/relations             - List relations
DELETE /registry/relations/{id}        - Delete relation

GET    /registry/tree                  - Hierarchical view
POST   /registry/merge                 - Merge duplicates
POST   /registry/import                - Batch import
POST   /registry/link-mention          - Link text mention
```

#### Page Anchoring Endpoints
```
POST   /page-anchors/detect            - Detect anchors on page
GET    /page-anchors/page/{doc}/{page} - Get page anchors
POST   /page-anchors/table-attachments/auto-attach - Auto attach tables
GET    /page-anchors/table-attachments/{doc}       - List attachments
PUT    /page-anchors/table-attachments/{id}/reassign - Reassign table
```

#### State & Rules Endpoints
```
POST   /state/compute                  - Compute entity state
GET    /state/entity/{id}              - Get entity state
GET    /state/conflicts/{id}           - Get conflicts
POST   /state/conflicts/{id}/resolve   - Resolve conflict
POST   /state/report/{id}              - Generate report

POST   /rules/create-from-event        - Rule from event
GET    /rules/                         - List rules
GET    /rules/{id}                     - Get rule details
PUT    /rules/{id}                     - Update rule
POST   /rules/{id}/test                - Test rule
DELETE /rules/{id}                     - Delete rule
```

### 4. Worker Layer (Celery)

#### Enhanced Pipelines
- `parse_worker` - PDF ? blocks with bbox, page structure
- `embed_worker` - Chunks ? embeddings with anchor awareness
- `extract_worker` - Text ? entities, relations, issues/actions/decisions
- `graph_worker` - Registry + embeddings ? Neo4j sync
- `rules_worker` - Apply learned rules to new documents

### 5. Search & Retrieval

#### Vector Search (Qdrant)
- Chunks indexed with metadata
- Anchor entity bias in retrieval
- Table context enrichment

#### Graph Search (Neo4j)
- Registry as primary graph
- Multi-hop relationship traversal
- Context expansion for queries

### 6. UI Layer (Next.js)

#### Components (NEW)
- `RegistryManager` - Create/edit/view entities
- `RulesManager` - Manage learned rules
- `StatusDashboard` - Object state with conflicts
- `PageViewer` - Table attachment reassignment
- `EntityTree` - Hierarchical registry view

## Data Flows

### 1. Document Ingestion ? Registry Anchoring
```
Upload PDF
  ?
Parse to blocks (Docling)
  ?
Detect anchors (regex + embedding match vs registry)
  ?
Auto-attach tables (proximity)
  ?
Chunks include anchor_entity_id + table_attachment_id
  ?
Search & reports use anchors for context
```

### 2. User Correction ? Rule ? Auto-Apply
```
User makes correction (curation_event)
  ?
RulesEngine.create_rule_from_event()
  ?
Rule stored in curation_rules
  ?
Next document ? RulePipeline applies rules
  ?
Auto-correction with full traceability
```

### 3. Claims ? State ? Conflicts ? Resolution
```
Extract claims from documents
  ?
StateAggregator.compute_state()
  ?
Detect competing claims per field
  ?
Create state_conflicts if competing_claims > 1
  ?
User resolves ? CLAIM_OVERRIDE rule created
  ?
Future states use override value
```

### 4. Query ? Entity Linking ? GraphRAG
```
User query
  ?
EntityLinker.link() ? seed entities
  ?
Graph expansion (1-2 hops via relations)
  ?
Fetch facts from subgraph
  ?
Combine with vector search
  ?
Ranked results with reasoning trace
```

## Key Concepts

### Entity Linking Scoring
```
score = max(
    exact_match: 1.0,
    alias_match: 0.95,
    fuzzy_match: ratio (0.75-1.0),
    anchor_bias: +0.3,
    embedding_similarity: 0.5-1.0,
    context_match: 0.4
)
```

### Disambiguation Strategy
```
if score[0] - score[1] < margin_threshold:
    ? Pending review (don't auto-link)
else:
    ? Use top candidate
```

### Rule Application
```
For each curation_rule (ordered by priority):
    if conditions_match(input):
        output = apply_rule(input)
        break
```

### State Conflict Detection
```
For each field in aggregated_claims:
    if competing_values > 1:
        ? Create state_conflict (open)
```

## Security & Integrity

### Idempotency
- All ingest tasks use SHA256 document hash
- Duplicate documents skipped
- Rule application is idempotent

### Auditability
- curation_events track all user changes
- Rules track created_from_event_id
- State conflicts track resolution_event_id

### Validation
- Registry entities have unique (project_key, type, entity_key)
- Relations enforce entity existence
- Constraints prevent invalid configurations

## Performance

### Indexing
```sql
registry_entities:
  - (project_key, status, type)
  - canonical_name
  - aliases (GIN index on JSONB)

page_anchors:
  - (doc_version_id, page_number)
  - registry_entity_id

table_attachments:
  - (doc_version_id, registry_entity_id)

curation_rules:
  - (project_key, rule_type, enabled, priority)
```

### Caching Strategy
- Registry in-memory for EntityLinker
- Context packs cached per project
- Rules prioritized for quick lookup

## Extensibility

### Adding New Rule Types
1. Add case to `RuleType` enum
2. Implement `apply_*_rules()` method
3. Add test cases
4. Document in API

### Adding New Entity Types
1. Add to registry entity types
2. Define constraints in registry_constraints
3. Create relations as needed
4. Update UI filters

### Custom Scoring Signals
1. Add `LinkingSignal` enum value
2. Compute in `_score_candidate()`
3. Update score aggregation logic
4. Add test case

## Testing Strategy

### Unit Tests
```
tests/test_linking.py     - EntityLinker scoring, disambiguation
tests/test_rules.py       - Rule application, conversion
tests/test_state.py       - State computation, conflict detection
tests/test_anchoring.py   - Anchor detection, auto-attachment
```

### Integration Tests
```
tests/integration/test_ingest_to_report.py
  - Full pipeline: ingest ? parse ? anchor ? extract ? state ? report

tests/integration/test_correction_learning.py
  - User correction ? rule ? auto-apply on next document

tests/integration/test_conflict_resolution.py
  - State conflicts ? user resolution ? override rule
```

### Evaluation Suite
```
eval/test_cases.json
??? transcript_correction_cases
??? entity_linking_cases
??? table_attachment_cases
??? state_aggregation_cases

eval/eval_runner.py - Run all test cases, report metrics
```

## Operations

### Monitoring
- Structured logs with correlation_id per pipeline run
- Curation event tracking
- Rule application metrics
- State conflict rate tracking

### Debugging
- `/debug/run/{correlation_id}` endpoint
- Full trace of entity linking steps
- Rule application details
- State computation breakdown

### Scaling
- Horizontal: parse_worker, embed_worker scale independently
- Vertical: Qdrant indexing, Neo4j clustering
- Cache: Registry context per project

## Future Enhancements

1. **Multi-language support** - Lexicon per language
2. **Temporal reasoning** - As-of-date state evolution
3. **Relationship learning** - Infer relations from extraction patterns
4. **Advanced disambiguation** - Active learning for ambiguous cases
5. **Custom scoring** - Per-project linking signal weights
6. **Visualization** - Interactive graph editor for registry
