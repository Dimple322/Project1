from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db import get_db, engine
from models import Base
from config import settings
from logger import get_logger
import schemas
import models
from typing import List, Optional
import os
import tempfile
import mimetypes
import json
from datetime import datetime

# Import new routers
from api.registry import router as registry_router
from api.page_anchors import router as page_anchors_router
from api.state_and_rules import state_router, rules_router

# Create tables
Base.metadata.create_all(bind=engine)

logger = get_logger(__name__)

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-RetryCount",
        "X-Requested-With",
    ],
    expose_headers=[
        "Content-Type",
        "Content-Length",
        "Content-Disposition",
    ],
    max_age=3600,
)

# Include new routers
app.include_router(registry_router)
app.include_router(page_anchors_router)
app.include_router(state_router)
app.include_router(rules_router)

# ============ INGEST ENDPOINTS ============

@app.post("/ingest/file", response_model=schemas.IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Upload and ingest a document file"""
    from storage import minio_client, compute_sha256
    from celery_app import parse_document_task
    
    try:
        logger.info(f"Ingesting file: {file.filename}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        try:
            # Compute SHA256
            sha256_hash = compute_sha256(temp_path)
            
            # Check if document already exists
            existing = db.query(models.Document).filter(
                models.Document.sha256_hash == sha256_hash
            ).first()
            
            if existing:
                return schemas.IngestResponse(
                    document_id=existing.id,
                    filename=existing.filename,
                    sha256_hash=existing.sha256_hash,
                    status="duplicate",
                    message="Document already exists"
                )
            
            # Upload to MinIO
            original_path = f"originals/{sha256_hash}/{file.filename}"
            minio_client.upload_file(temp_path, original_path)
            
            # Create document record
            doc = models.Document(
                filename=file.filename,
                mime_type=file.content_type or "application/octet-stream",
                file_size=len(content),
                original_path=original_path,
                sha256_hash=sha256_hash
            )
            db.add(doc)
            db.flush()
            
            # Create first version
            version = models.DocumentVersion(
                document_id=doc.id,
                version_number=1,
                parsing_status="pending"
            )
            db.add(version)
            db.commit()
            
            logger.info(f"Document created: {doc.id}, version: {version.id}")
            
            # Trigger async parsing
            if background_tasks:
                background_tasks.add_task(parse_document_task.delay, doc.id, version.id)
            else:
                parse_document_task.delay(doc.id, version.id)
            
            return schemas.IngestResponse(
                document_id=doc.id,
                filename=doc.filename,
                sha256_hash=doc.sha256_hash,
                status="ingested",
                message="Document ingested successfully"
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all documents"""
    documents = db.query(models.Document).offset(skip).limit(limit).all()
    total = db.query(models.Document).count()
    
    return {
        "documents": [schemas.DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            sha256_hash=doc.sha256_hash,
            parsing_status=doc.versions[0].parsing_status if doc.versions else "unknown",
            chunk_count=doc.versions[0].chunk_count if doc.versions else 0,
            created_at=doc.created_at
        ) for doc in documents],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details"""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return schemas.DocumentSchema.from_orm(doc)

# ============ SEARCH ENDPOINTS ============

@app.post("/search", response_model=schemas.SearchResponse)
async def search(
    request: schemas.SearchRequest,
    db: Session = Depends(get_db)
):
    """Search documents using vector similarity with Qdrant"""
    from embeddings import EmbeddingService
    from qdrant_client import QdrantClient
    
    try:
        logger.info(f"Searching: {request.query}")
        
        # Generate query embedding
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.embed_text(request.query)
        
<<<<<<< Updated upstream
        # Search in Qdrant using query_points
=======
        # Search in Qdrant using query_points (qdrant-client 1.16.2)
>>>>>>> Stashed changes
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        qdrant_key = os.getenv("QDRANT_API_KEY", "qdrant_key")
        
        qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        
<<<<<<< Updated upstream
        # Use query_points for qdrant-client 1.16.x
        search_response = qdrant.query_points(
=======
        # Use query_points for qdrant-client 1.16.2
        search_results = qdrant.query_points(
>>>>>>> Stashed changes
            collection_name="documents",
            query=query_embedding,
            limit=request.limit,
            with_payload=True
<<<<<<< Updated upstream
        )
        search_results = search_response.points if hasattr(search_response, "points") else search_response
=======
        ).points
>>>>>>> Stashed changes
        
        # Build results
        results = []
        for result in search_results:
<<<<<<< Updated upstream
            payload = result.payload if hasattr(result, "payload") else result.get("payload", {})
            score = result.score if hasattr(result, "score") else result.get("score", 0.0)
=======
            payload = result.payload if hasattr(result, 'payload') else {}
>>>>>>> Stashed changes
            
            results.append(schemas.SearchResult(
                chunk_id=payload.get("chunk_id", ""),
                document_id=payload.get("doc_id", ""),
                text=payload.get("text", "")[:500],  # Truncate for API response
<<<<<<< Updated upstream
                score=float(score),
=======
                score=float(result.score) if hasattr(result, 'score') else 0.0,
>>>>>>> Stashed changes
                page_number=payload.get("page_number"),
                section_path=payload.get("section_path")
            ))
        
        logger.info(f"Search returned {len(results)} results")
        
        return schemas.SearchResponse(
            results=results,
            total=len(results),
            limit=request.limit,
            offset=request.offset
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    RAG endpoint: search documents + generate answer using LLM
    
    Request: {
        "question": "What is...",
        "max_context_chunks": 3
    }
    """
    from embeddings import EmbeddingService
    from qdrant_client import QdrantClient
    from llm import get_llm_client
    
    try:
        question = request.get("question", "")
        max_chunks = request.get("max_context_chunks", 3)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question required")
        
        logger.info(f"Ask: {question}")
        
        # 1. Search for relevant chunks using Qdrant
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.embed_text(question)
        
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        qdrant_key = os.getenv("QDRANT_API_KEY", "qdrant_key")
        qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        
<<<<<<< Updated upstream
        search_response = qdrant.query_points(
=======
        # Use query_points for qdrant-client 1.16.2
        search_results = qdrant.query_points(
>>>>>>> Stashed changes
            collection_name="documents",
            query=query_embedding,
            limit=max_chunks,
            with_payload=True
<<<<<<< Updated upstream
        )
        search_results = search_response.points if hasattr(search_response, "points") else search_response
=======
        ).points
>>>>>>> Stashed changes
        
        # 2. Build context from search results
        context_chunks = []
        sources = []
        
        for result in search_results:
<<<<<<< Updated upstream
            payload = result.payload if hasattr(result, "payload") else result.get("payload", {})
=======
            payload = result.payload if hasattr(result, 'payload') else {}
>>>>>>> Stashed changes
            chunk_text = payload.get("text", "")
            doc_id = payload.get("doc_id", "")
            score = float(result.score) if hasattr(result, 'score') else 0.0
            
            if chunk_text:
                context_chunks.append(chunk_text)
                
                # Get document name
                doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
                if doc and doc.filename not in [s["filename"] for s in sources]:
                    score = result.score if hasattr(result, "score") else result.get("score", 0.0)
                    sources.append({
                        "filename": doc.filename,
                        "doc_id": doc_id,
<<<<<<< Updated upstream
                        "score": float(score)
=======
                        "score": score
>>>>>>> Stashed changes
                    })
        
        context = "\n---\n".join(context_chunks) if context_chunks else ""
        
        # 3. Generate answer using LLM
        llm = get_llm_client()
        
        if not llm.is_available():
<<<<<<< Updated upstream
            logger.warning(f"LLM not available: {llm.last_error or 'unknown error'}")
=======
            logger.warning("LLM not available, returning search-only response")
>>>>>>> Stashed changes
            return {
                "answer": "LLM service is not available. Here are the most relevant documents instead:",
                "search_results": [
                    {
                        "text": chunk[:200],
                        "doc_id": sources[i]["doc_id"] if i < len(sources) else "",
                        "filename": sources[i]["filename"] if i < len(sources) else ""
                    } 
                    for i, chunk in enumerate(context_chunks)
                ],
                "sources": sources,
                "status": "search_only",
                "warning": "LLM unavailable"
            }
        
        answer = llm.answer(question, context)
        if not answer:
            logger.warning(f"LLM returned no answer: {llm.last_error or 'unknown error'}")
            return {
                "answer": "LLM service is not available. Search results available instead.",
                "search_results": [{"text": chunk, "doc_id": sources[i]["doc_id"] if i < len(sources) else ""} for i, chunk in enumerate(context_chunks)],
                "sources": sources,
                "status": "search_only"
            }
        
        return {
            "answer": answer or "Could not generate answer",
            "sources": sources,
            "context_chunks": len(context_chunks),
            "status": "success" if answer else "llm_error"
        }
    
    except Exception as e:
        logger.error(f"Ask error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
async def get_knowledge_graph(
    document_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get knowledge graph: nodes (documents, chunks, entities) and edges (relationships)
    
    Optional: filter by document_id
    """
    from neo4j import GraphDatabase
    
    try:
        neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "neo4j_password")
        
        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_pass))
        
        nodes = []
        edges = []
        
        with driver.session() as session:
            # Get nodes
            query_nodes = """
            MATCH (n)
            """
            if document_id:
                query_nodes += f" WHERE n.document_id = '{document_id}' OR n.id = '{document_id}'"
            
            query_nodes += f" RETURN n LIMIT {limit}"
            
            for record in session.run(query_nodes):
                node = record["n"]
                nodes.append({
                    "id": node.get("id") or node.get("chunk_id") or str(hash(str(node))),
                    "label": node.get("text", "")[:50] if node.get("text") else node.get("entity", ""),
                    "type": node.get("type", "unknown"),
                    "properties": dict(node)
                })
            
            # Get edges
            query_edges = """
            MATCH (a)-[r]->(b)
            """
            if document_id:
                query_edges += f" WHERE a.document_id = '{document_id}' OR a.id = '{document_id}'"
            
            query_edges += f" RETURN a, r, b LIMIT {limit}"
            
            for record in session.run(query_edges):
                a = record["a"]
                r = record["r"]
                b = record["b"]
                
                edges.append({
                    "source": a.get("id") or a.get("chunk_id") or str(hash(str(a))),
                    "target": b.get("id") or b.get("chunk_id") or str(hash(str(b))),
                    "type": r.type,
                    "label": r.type
                })
        
        driver.close()
        
        logger.info(f"Graph: {len(nodes)} nodes, {len(edges)} edges")
        
        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    
    except Exception as e:
        logger.warning(f"Knowledge graph not available: {e}")
        return {
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "total_edges": 0,
            "warning": "Neo4j not configured or error occurred"
        }

# ============ TRANSCRIPT ENDPOINTS ============

@app.post("/transcript/correct")
async def correct_transcript(
    request: schemas.TranscriptCorrectionRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Correct transcript using lexicon"""
    from celery_app import correct_transcript_task
    
    doc = db.query(models.Document).filter(models.Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if background_tasks:
        background_tasks.add_task(correct_transcript_task.delay, request.document_id)
    else:
        correct_transcript_task.delay(request.document_id)
    
    return {"status": "processing", "message": "Transcript correction started"}

@app.get("/transcript/{document_id}")
async def get_transcript(document_id: str, db: Session = Depends(get_db)):
    """Get transcript correction"""
    correction = db.query(models.TranscriptCorrection).filter(
        models.TranscriptCorrection.document_id == document_id
    ).first()
    
    if not correction:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return schemas.TranscriptCorrectionResponse(
        document_id=correction.document_id,
        original_text=correction.original_text,
        corrected_text=correction.corrected_text,
        diff=correction.diff,
        correction_status=correction.correction_status
    )

# ============ LEXICON ENDPOINTS ============

@app.post("/lexicon")
async def create_lexicon_entry(
    entry: schemas.LexiconCreate,
    db: Session = Depends(get_db)
):
    """Create lexicon entry"""
    lex = models.Lexicon(**entry.dict())
    db.add(lex)
    db.commit()
    db.refresh(lex)
    return schemas.LexiconSchema.from_orm(lex)

@app.get("/lexicon")
async def list_lexicon(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List lexicon entries"""
    query = db.query(models.Lexicon)
    if category:
        query = query.filter(models.Lexicon.category == category)
    
    entries = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "entries": [schemas.LexiconSchema.from_orm(e) for e in entries],
        "total": total
    }

# ============ ENTITY ENDPOINTS ============

@app.post("/entities/projects")
async def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create project"""
    proj = models.Project(**project.dict())
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return schemas.ProjectSchema.from_orm(proj)

@app.get("/entities/projects")
async def list_projects(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List projects"""
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    total = db.query(models.Project).count()
    
    return {
        "projects": [schemas.ProjectSchema.from_orm(p) for p in projects],
        "total": total
    }

@app.post("/entities/phases")
async def create_phase(
    phase: schemas.PhaseCreate,
    db: Session = Depends(get_db)
):
    """Create phase"""
    ph = models.Phase(**phase.dict())
    db.add(ph)
    db.commit()
    db.refresh(ph)
    return schemas.PhaseSchema.from_orm(ph)

@app.post("/entities/facilities")
async def create_facility(
    facility: schemas.FacilityCreate,
    db: Session = Depends(get_db)
):
    """Create facility"""
    fac = models.Facility(**facility.dict())
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return schemas.FacilitySchema.from_orm(fac)

@app.post("/entities/wells")
async def create_well(
    well: schemas.WellCreate,
    db: Session = Depends(get_db)
):
    """Create well"""
    w = models.Well(**well.dict())
    db.add(w)
    db.commit()
    db.refresh(w)
    return schemas.WellSchema.from_orm(w)

@app.post("/entities/subsystems")
async def create_subsystem(
    subsystem: schemas.SubsystemCreate,
    db: Session = Depends(get_db)
):
    """Create subsystem"""
    sub = models.Subsystem(**subsystem.dict())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return schemas.SubsystemSchema.from_orm(sub)

# ============ ISSUES/ACTIONS/DECISIONS ENDPOINTS ============

@app.post("/issues")
async def create_issue(
    issue: schemas.IssueCreate,
    db: Session = Depends(get_db)
):
    """Create issue"""
    iss = models.Issue(**issue.dict())
    db.add(iss)
    db.commit()
    db.refresh(iss)
    return schemas.IssueSchema.from_orm(iss)

@app.get("/issues")
async def list_issues(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    is_pending_review: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List issues"""
    query = db.query(models.Issue)
    if status:
        query = query.filter(models.Issue.status == status)
    if is_pending_review is not None:
        query = query.filter(models.Issue.is_pending_review == is_pending_review)
    
    issues = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "issues": [schemas.IssueSchema.from_orm(i) for i in issues],
        "total": total
    }

@app.post("/actions")
async def create_action(
    action: schemas.ActionItemCreate,
    db: Session = Depends(get_db)
):
    """Create action item"""
    act = models.ActionItem(**action.dict())
    db.add(act)
    db.commit()
    db.refresh(act)
    return schemas.ActionItemSchema.from_orm(act)

@app.get("/actions")
async def list_actions(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    is_pending_review: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List action items"""
    query = db.query(models.ActionItem)
    if status:
        query = query.filter(models.ActionItem.status == status)
    if is_pending_review is not None:
        query = query.filter(models.ActionItem.is_pending_review == is_pending_review)
    
    actions = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "actions": [schemas.ActionItemSchema.from_orm(a) for a in actions],
        "total": total
    }

@app.post("/decisions")
async def create_decision(
    decision: schemas.DecisionCreate,
    db: Session = Depends(get_db)
):
    """Create decision"""
    dec = models.Decision(**decision.dict())
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return schemas.DecisionSchema.from_orm(dec)

@app.get("/decisions")
async def list_decisions(
    skip: int = 0,
    limit: int = 10,
    is_pending_review: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List decisions"""
    query = db.query(models.Decision)
    if is_pending_review is not None:
        query = query.filter(models.Decision.is_pending_review == is_pending_review)
    
    decisions = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "decisions": [schemas.DecisionSchema.from_orm(d) for d in decisions],
        "total": total
    }

# ============ CURATION ENDPOINTS ============

@app.post("/curation/event")
async def create_curation_event(
    event: schemas.CurationEventCreate,
    db: Session = Depends(get_db)
):
    """Create curation event"""
    cur_event = models.CurationEvent(**event.dict())
    db.add(cur_event)
    db.commit()
    db.refresh(cur_event)
    return schemas.CurationEventSchema.from_orm(cur_event)

@app.get("/curation/events")
async def list_curation_events(
    skip: int = 0,
    limit: int = 10,
    event_type: Optional[str] = None,
    applied: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List curation events"""
    query = db.query(models.CurationEvent)
    if event_type:
        query = query.filter(models.CurationEvent.event_type == event_type)
    if applied is not None:
        query = query.filter(models.CurationEvent.applied == applied)
    
    events = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "events": [schemas.CurationEventSchema.from_orm(e) for e in events],
        "total": total
    }

# ============ REPORTS ENDPOINTS ============

@app.get("/reports/status/{subject_type}/{subject_id}")
async def get_status_card(
    subject_type: str,
    subject_id: str,
    db: Session = Depends(get_db)
):
    """Get status card for a subject"""
    # Get subject name
    subject_name = ""
    if subject_type == "facility":
        facility = db.query(models.Facility).filter(models.Facility.id == subject_id).first()
        subject_name = facility.name if facility else "Unknown"
    elif subject_type == "subsystem":
        subsystem = db.query(models.Subsystem).filter(models.Subsystem.id == subject_id).first()
        subject_name = subsystem.name if subsystem else "Unknown"
    elif subject_type == "well":
        well = db.query(models.Well).filter(models.Well.id == subject_id).first()
        subject_name = well.name if well else "Unknown"
    
    # Get claims
    claims = db.query(models.Claim).filter(
        models.Claim.subject_id == subject_id,
        models.Claim.subject_type == subject_type
    ).all()
    
    # Get issues
    if subject_type == "subsystem":
        issues = db.query(models.Issue).filter(models.Issue.subsystem_id == subject_id).all()
    elif subject_type == "well":
        issues = db.query(models.Issue).filter(models.Issue.well_id == subject_id).all()
    else:
        issues = []
    
    # Get actions and decisions (general)
    actions = db.query(models.ActionItem).all()
    decisions = db.query(models.Decision).all()
    
    return schemas.StatusCard(
        subject_id=subject_id,
        subject_type=subject_type,
        subject_name=subject_name,
        claims=[{
            "id": c.id,
            "text": c.claim_text,
            "confidence": c.confidence,
            "created_at": c.created_at
        } for c in claims],
        issues=[{
            "id": i.id,
            "title": i.title,
            "status": i.status,
            "priority": i.priority,
            "confidence": i.confidence,
            "created_at": i.created_at
        } for i in issues],
        actions=[{
            "id": a.id,
            "title": a.title,
            "status": a.status,
            "confidence": a.confidence,
            "created_at": a.created_at
        } for a in actions],
        decisions=[{
            "id": d.id,
            "title": d.title,
            "confidence": d.confidence,
            "created_at": d.created_at
        } for d in decisions],
        last_updated=datetime.utcnow()
    )

# ============ PENDING REVIEW ENDPOINTS ============

@app.get("/pending-review")
async def get_pending_review(
    db: Session = Depends(get_db)
):
    """Get all items pending review"""
    pending_issues = db.query(models.Issue).filter(models.Issue.is_pending_review == True).all()
    pending_actions = db.query(models.ActionItem).filter(models.ActionItem.is_pending_review == True).all()
    pending_decisions = db.query(models.Decision).filter(models.Decision.is_pending_review == True).all()
    
    return {
        "issues": [schemas.IssueSchema.from_orm(i) for i in pending_issues],
        "actions": [schemas.ActionItemSchema.from_orm(a) for a in pending_actions],
        "decisions": [schemas.DecisionSchema.from_orm(d) for d in pending_decisions],
        "total": len(pending_issues) + len(pending_actions) + len(pending_decisions)
    }

@app.post("/pending-review/approve/{item_type}/{item_id}")
async def approve_item(
    item_type: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """Approve pending item"""
    if item_type == "issue":
        item = db.query(models.Issue).filter(models.Issue.id == item_id).first()
    elif item_type == "action":
        item = db.query(models.ActionItem).filter(models.ActionItem.id == item_id).first()
    elif item_type == "decision":
        item = db.query(models.Decision).filter(models.Decision.id == item_id).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid item type")
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item.is_pending_review = False
    db.commit()
    
    return {"status": "approved"}

@app.delete("/pending-review/{item_type}/{item_id}")
async def reject_item(
    item_type: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """Reject and delete pending item"""
    if item_type == "issue":
        item = db.query(models.Issue).filter(models.Issue.id == item_id).first()
    elif item_type == "action":
        item = db.query(models.ActionItem).filter(models.ActionItem.id == item_id).first()
    elif item_type == "decision":
        item = db.query(models.Decision).filter(models.Decision.id == item_id).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid item type")
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    
    return {"status": "rejected"}

# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "version": settings.API_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
