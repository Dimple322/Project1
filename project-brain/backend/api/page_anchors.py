"""
Page Anchoring and Table Attachment API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from db import get_db
import models
from knowledge.page_anchoring import AnchorDetector, TableAttachmentService, PageStructureParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/page-anchors", tags=["page-anchors"])


@router.post("/detect")
async def detect_anchors(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Detect anchors on a PDF page"""
    
    doc_version_id = request.get("doc_version_id")
    page_number = request.get("page_number")
    page_text = request.get("page_text")
    blocks = request.get("blocks", [])
    project_key = request.get("project_key", "default")
    
    detector = AnchorDetector(db, project_key)
    
    anchors = detector.detect_anchors(
        doc_version_id=doc_version_id,
        page_number=page_number,
        page_text=page_text,
        blocks=blocks
    )
    
    return {
        "page_number": page_number,
        "detected_anchors": len(anchors),
        "anchors": anchors[:10]  # Limit response
    }


@router.get("/page/{doc_version_id}/{page_number}")
async def get_page_anchors(
    doc_version_id: str,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Get anchors on a specific page"""
    
    anchors = db.query(models.PageAnchor).filter(
        models.PageAnchor.doc_version_id == doc_version_id,
        models.PageAnchor.page_number == page_number
    ).all()
    
    return {
        "page_number": page_number,
        "anchors": [
            {
                "id": a.id,
                "anchor_text": a.anchor_text,
                "registry_entity_id": a.registry_entity_id,
                "confidence": a.confidence,
                "bbox": a.bbox
            }
            for a in anchors
        ]
    }


@router.post("/table-attachments/auto-attach")
async def auto_attach_tables(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Automatically attach tables to entities"""
    
    doc_version_id = request.get("doc_version_id")
    page_number = request.get("page_number")
    blocks = request.get("blocks", [])
    anchors = request.get("anchors", [])
    project_key = request.get("project_key", "default")
    
    service = TableAttachmentService(db, project_key)
    
    attachment_ids = service.auto_attach_tables(
        doc_version_id=doc_version_id,
        page_number=page_number,
        blocks=blocks,
        anchors=anchors
    )
    
    return {
        "attached_count": len(attachment_ids),
        "attachment_ids": attachment_ids
    }


@router.get("/table-attachments/{doc_version_id}")
async def get_table_attachments(
    doc_version_id: str,
    page_number: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get table attachments for a document"""
    
    query = db.query(models.TableAttachment).filter(
        models.TableAttachment.doc_version_id == doc_version_id
    )
    
    if page_number:
        query = query.filter(models.TableAttachment.page_number == page_number)
    
    attachments = query.all()
    
    return {
        "doc_version_id": doc_version_id,
        "attachments": [
            {
                "id": a.id,
                "page_number": a.page_number,
                "block_id": a.block_id,
                "registry_entity_id": a.registry_entity_id,
                "confidence": a.confidence,
                "anchor_id": a.anchor_id,
                "source": a.source
            }
            for a in attachments
        ]
    }


@router.put("/table-attachments/{attachment_id}/reassign")
async def reassign_table_attachment(
    attachment_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Manually reassign a table to different entity"""
    
    new_entity_id = request.get("registry_entity_id")
    project_key = request.get("project_key", "default")
    user_id = request.get("user_id", "system")
    
    service = TableAttachmentService(db, project_key)
    
    try:
        event_id = service.manual_attachment(
            table_attachment_id=attachment_id,
            new_registry_entity_id=new_entity_id,
            user_id=user_id
        )
        
        return {
            "attachment_id": attachment_id,
            "new_entity_id": new_entity_id,
            "event_id": event_id,
            "status": "reassigned"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/page-blocks")
async def create_page_block(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a page block record"""
    
    block = models.DocPageBlock(
        id=str(uuid.uuid4()),
        doc_version_id=request.get("doc_version_id"),
        page_number=request.get("page_number"),
        block_type=request.get("block_type"),
        text_content=request.get("text_content"),
        bbox=request.get("bbox"),
        block_order=request.get("block_order", 0),
        metadata=request.get("metadata", {}),
        created_at=datetime.utcnow()
    )
    
    db.add(block)
    db.commit()
    
    return {
        "id": block.id,
        "status": "created"
    }


@router.get("/page-blocks/{doc_version_id}")
async def get_page_blocks(
    doc_version_id: str,
    page_number: Optional[int] = Query(None),
    block_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get page blocks for a document"""
    
    query = db.query(models.DocPageBlock).filter(
        models.DocPageBlock.doc_version_id == doc_version_id
    )
    
    if page_number:
        query = query.filter(models.DocPageBlock.page_number == page_number)
    
    if block_type:
        query = query.filter(models.DocPageBlock.block_type == block_type)
    
    blocks = query.order_by(models.DocPageBlock.page_number, models.DocPageBlock.block_order).all()
    
    return {
        "doc_version_id": doc_version_id,
        "blocks": [
            {
                "id": b.id,
                "page_number": b.page_number,
                "block_type": b.block_type,
                "text_content": b.text_content[:100] if b.text_content else None,
                "bbox": b.bbox
            }
            for b in blocks
        ]
    }
