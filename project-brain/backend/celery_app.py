import os
from celery import Celery
from config import settings
from logger import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    'project_brain',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

@celery_app.task(bind=True, max_retries=3)
def parse_document_task(self, document_id: str, version_id: str):
    """Parse document and extract chunks"""
    import sys
    import json
    import tempfile
    
    # Ensure /app is in path for imports
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')
    
    from db import SessionLocal
    from models import Document, DocumentVersion, Chunk
    from parsing import DocumentParser
    from storage import minio_client, compute_sha256_bytes
    
    db = SessionLocal()
    try:
        logger.info(f"Starting document parsing: {document_id}")
        
        # Get document and version
        doc = db.query(Document).filter(Document.id == document_id).first()
        version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
        
        if not doc or not version:
            logger.error(f"Document or version not found: {document_id}, {version_id}")
            return
        
        # Download original file from MinIO
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            minio_client.download_file(doc.original_path, tmp.name)
            temp_file_path = tmp.name
        
        try:
            # Parse document
            parse_result = DocumentParser.parse_file(temp_file_path, doc.mime_type)
            
            if parse_result["status"] != "success":
                version.parsing_status = "failed"
                version.parsing_error = parse_result.get("error", "Unknown error")
                db.commit()
                logger.error(f"Parsing failed for {document_id}: {version.parsing_error}")
                return
            
            # Save parsed result to MinIO
            parsed_data = {
                "document_id": document_id,
                "version_number": version.version_number,
                "chunks": parse_result.get("chunks", []),
                "parser": parse_result.get("parser", "unknown"),
                "page_count": parse_result.get("page_count", 0)
            }
            
            parsed_json = json.dumps(parsed_data, ensure_ascii=False, indent=2)
            parsed_path = f"parsed/{document_id}/v{version.version_number}/parsed.json"
            minio_client.upload_bytes(parsed_json.encode(), parsed_path)
            
            # Create chunks in database
            chunks = parse_result.get("chunks", [])
            for chunk_num, chunk_data in enumerate(chunks):
                chunk = Chunk(
                    document_id=document_id,
                    version_id=version_id,
                    chunk_number=chunk_num,
                    text_content=chunk_data.get("text", ""),
                    page_number=chunk_data.get("page_number"),
                    section_path=chunk_data.get("section_path")
                )
                db.add(chunk)
            
            # Update version
            version.parsing_status = "completed"
            version.parsed_path = parsed_path
            version.chunk_count = len(chunks)
            version.parsing_metadata = {
                "parser": parse_result.get("parser"),
                "page_count": parse_result.get("page_count", 0)
            }
            
            db.commit()
            logger.info(f"Successfully parsed document {document_id}: {len(chunks)} chunks")
            
            # Trigger embedding task for all chunks
            from celery_app import embed_chunks_task
            embed_chunks_task.delay(document_id, version_id)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error parsing document {document_id}: {e}")
        version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
        if version:
            version.parsing_status = "failed"
            version.parsing_error = str(e)
            db.commit()
        
        # Retry
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for document {document_id}")
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def embed_chunks_task(self, document_id: str, version_id: str):
    """Generate embeddings for document chunks"""
    from db import SessionLocal
    from models import Chunk
    from embeddings import EmbeddingService
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance
    import uuid
    
    db = SessionLocal()
    try:
        logger.info(f"Starting embedding for chunks: {document_id}")
        
        # Get all chunks
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document_id,
            Chunk.version_id == version_id
        ).all()
        
        if not chunks:
            logger.info(f"No chunks found for {document_id}")
            return
        
        # Initialize services
        embedding_service = EmbeddingService()
        qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
    api_key=os.getenv("QDRANT_API_KEY"),
)
        
        # Check/create collection
        collection_name = "documents"
        try:
            qdrant.get_collection(collection_name)
        except:
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
        
        # Generate embeddings and upsert to Qdrant
        points = []
        for chunk in chunks:
            embedding = embedding_service.embed_text(chunk.text_content)
            point_id = str(uuid.uuid4())
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "doc_id": document_id,
                    "version_id": version_id,
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                    "section_path": chunk.section_path,
                    "text": chunk.text_content[:500]
                }
            ))
            
            # Update chunk with vector ID
            chunk.embedding_vector_id = point_id
            chunk.is_embedded = True
        
        # Upsert to Qdrant
        qdrant.upsert(collection_name=collection_name, points=points)
        db.commit()
        
        logger.info(f"Embedded {len(chunks)} chunks for {document_id}")
        
    except Exception as e:
        logger.error(f"Error embedding chunks for {document_id}: {e}")
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for embedding {document_id}")
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def correct_transcript_task(self, document_id: str):
    """Correct transcript using lexicon"""
    from db import SessionLocal
    from models import Document, DocumentVersion, TranscriptCorrection
    from transcript_corrector import TranscriptCorrector
    from storage import minio_client
    import json
    
    db = SessionLocal()
    try:
        logger.info(f"Starting transcript correction: {document_id}")
        
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document not found: {document_id}")
            return
        
        # Get latest version
        version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        
        if not version or not version.parsed_path:
            logger.error(f"No parsed version found for {document_id}")
            return
        
        # Get parsed content
        parsed_bytes = minio_client.download_bytes(version.parsed_path)
        parsed_data = json.loads(parsed_bytes.decode())
        
        # Combine all chunks
        full_text = "\n".join([chunk["text"] for chunk in parsed_data.get("chunks", [])])
        
        # Correct transcript
        correction_result = TranscriptCorrector.correct_transcript(full_text, db)
        
        # Save correction
        transcript_correction = TranscriptCorrection(
            document_id=document_id,
            original_text=correction_result["original_text"],
            corrected_text=correction_result["corrected_text"],
            diff=correction_result["edits"],
            correction_status=correction_result["correction_status"]
        )
        db.add(transcript_correction)
        db.commit()
        
        logger.info(f"Corrected transcript for {document_id}: {correction_result['total_corrections']} corrections")
        
        # Trigger meeting extraction
        from celery_app import extract_meeting_task
        extract_meeting_task.delay(document_id)
        
    except Exception as e:
        logger.error(f"Error correcting transcript {document_id}: {e}")
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for transcript correction {document_id}")
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3)
def extract_meeting_task(self, document_id: str):
    """Extract meeting items from transcript"""
    from db import SessionLocal
    from models import Document, DocumentVersion, Chunk, Issue, ActionItem, Decision
    from meeting_extractor import MeetingExtractor
    from storage import minio_client
    import json
    
    db = SessionLocal()
    try:
        logger.info(f"Starting meeting extraction: {document_id}")
        
        # Get latest version
        version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        
        if not version:
            logger.error(f"No version found for {document_id}")
            return
        
        # Get all chunks
        chunks = db.query(Chunk).filter(Chunk.version_id == version.id).all()
        
        for chunk in chunks:
            # Extract meeting items
            extracted = MeetingExtractor.extract_from_transcript(
                chunk.text_content,
                chunk.id,
                db
            )
            
            # Save issues
            for issue_data in extracted.get("issues", []):
                issue = Issue(**issue_data)
                db.add(issue)
            
            # Save action items
            for action_data in extracted.get("actions", []):
                action = ActionItem(**action_data)
                db.add(action)
            
            # Save decisions
            for decision_data in extracted.get("decisions", []):
                decision = Decision(**decision_data)
                db.add(decision)
        
        db.commit()
        logger.info(f"Extracted meeting items from {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error extracting meeting items from {document_id}: {e}")
        try:
            self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for meeting extraction {document_id}")
    finally:
        db.close()
