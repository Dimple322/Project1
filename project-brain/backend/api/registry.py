"""
Registry Management Endpoints
Canonical project entity management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from db import get_db
import models
import schemas
from knowledge.linking_v2 import EntityLinker
from knowledge.rules_engine import CurationRulesEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["registry"])


# ========== ENTITY ENDPOINTS ==========

@router.post("/entities", response_model=Dict[str, Any])
async def create_registry_entity(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a registry entity"""
    
    project_key = request.get("project_key", "default")
    
    # Validate uniqueness
    existing = db.query(models.RegistryEntity).filter(
        models.RegistryEntity.project_key == project_key,
        models.RegistryEntity.type == request.get("type"),
        models.RegistryEntity.canonical_name == request.get("canonical_name")
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Entity already exists: {request.get('canonical_name')}"
        )
    
    entity = models.RegistryEntity(
        id=str(uuid.uuid4()),
        project_key=project_key,
        entity_key=request.get("entity_key", request.get("canonical_name").lower().replace(" ", "_")),
        type=request.get("type"),
        canonical_name=request.get("canonical_name"),
        aliases=request.get("aliases", []),
        attributes=request.get("attributes", {}),
        description=request.get("description"),
        status=request.get("status", "active"),
        owner_person_id=request.get("owner_person_id"),
        parent_id=request.get("parent_id"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=request.get("created_by", "system"),
        updated_by=request.get("updated_by", "system")
    )
    
    db.add(entity)
    db.commit()
    
    logger.info(f"Created registry entity: {entity.id} ({entity.canonical_name})")
    
    return {
        "id": entity.id,
        "project_key": entity.project_key,
        "canonical_name": entity.canonical_name,
        "type": entity.type,
        "status": "created"
    }


@router.get("/entities", response_model=List[Dict[str, Any]])
async def list_registry_entities(
    project_key: str = Query("default"),
    entity_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List registry entities with filters"""
    
    query = db.query(models.RegistryEntity).filter(
        models.RegistryEntity.project_key == project_key
    )
    
    if entity_type:
        query = query.filter(models.RegistryEntity.type == entity_type)
    
    if status:
        query = query.filter(models.RegistryEntity.status == status)
    
    if q:
        q_lower = q.lower()
        query = query.filter(
            (models.RegistryEntity.canonical_name.ilike(f"%{q}%")) |
            (models.RegistryEntity.description.ilike(f"%{q}%"))
        )
    
    entities = query.all()
    
    return [
        {
            "id": e.id,
            "canonical_name": e.canonical_name,
            "type": e.type,
            "aliases": e.aliases,
            "status": e.status,
            "owner_person_id": e.owner_person_id,
            "parent_id": e.parent_id
        }
        for e in entities
    ]


@router.get("/entities/{entity_id}", response_model=Dict[str, Any])
async def get_registry_entity(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get registry entity details"""
    
    entity = db.query(models.RegistryEntity).filter_by(id=entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return {
        "id": entity.id,
        "project_key": entity.project_key,
        "canonical_name": entity.canonical_name,
        "type": entity.type,
        "aliases": entity.aliases,
        "attributes": entity.attributes,
        "description": entity.description,
        "status": entity.status,
        "owner_person_id": entity.owner_person_id,
        "parent_id": entity.parent_id,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat()
    }


@router.put("/entities/{entity_id}", response_model=Dict[str, Any])
async def update_registry_entity(
    entity_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update registry entity"""
    
    entity = db.query(models.RegistryEntity).filter_by(id=entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Update fields
    for field in ["aliases", "attributes", "description", "status", "owner_person_id", "parent_id"]:
        if field in request:
            setattr(entity, field, request[field])
    
    entity.updated_at = datetime.utcnow()
    entity.updated_by = request.get("updated_by", "system")
    
    db.add(entity)
    db.commit()
    
    return {"id": entity.id, "status": "updated"}


@router.delete("/entities/{entity_id}")
async def delete_registry_entity(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Archive (soft delete) registry entity"""
    
    entity = db.query(models.RegistryEntity).filter_by(id=entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity.status = "archived"
    entity.updated_at = datetime.utcnow()
    
    db.add(entity)
    db.commit()
    
    return {"id": entity.id, "status": "archived"}


# ========== RELATION ENDPOINTS ==========

@router.post("/relations", response_model=Dict[str, Any])
async def create_registry_relation(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a relation between entities"""
    
    project_key = request.get("project_key", "default")
    
    # Check entities exist
    from_entity = db.query(models.RegistryEntity).filter_by(
        id=request.get("from_entity_id")
    ).first()
    to_entity = db.query(models.RegistryEntity).filter_by(
        id=request.get("to_entity_id")
    ).first()
    
    if not from_entity or not to_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check uniqueness
    existing = db.query(models.RegistryRelation).filter(
        models.RegistryRelation.from_entity_id == request.get("from_entity_id"),
        models.RegistryRelation.to_entity_id == request.get("to_entity_id"),
        models.RegistryRelation.relation_type == request.get("relation_type")
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Relation already exists")
    
    relation = models.RegistryRelation(
        id=str(uuid.uuid4()),
        project_key=project_key,
        from_entity_id=request.get("from_entity_id"),
        to_entity_id=request.get("to_entity_id"),
        relation_type=request.get("relation_type"),
        attributes=request.get("attributes", {}),
        confidence=request.get("confidence", 1.0),
        source=request.get("source", "manual"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(relation)
    db.commit()
    
    return {"id": relation.id, "status": "created"}


@router.get("/relations", response_model=List[Dict[str, Any]])
async def list_relations(
    project_key: str = Query("default"),
    from_entity_id: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List relations"""
    
    query = db.query(models.RegistryRelation).filter(
        models.RegistryRelation.project_key == project_key
    )
    
    if from_entity_id:
        query = query.filter(models.RegistryRelation.from_entity_id == from_entity_id)
    
    if relation_type:
        query = query.filter(models.RegistryRelation.relation_type == relation_type)
    
    relations = query.all()
    
    return [
        {
            "id": r.id,
            "from_entity_id": r.from_entity_id,
            "to_entity_id": r.to_entity_id,
            "relation_type": r.relation_type,
            "confidence": r.confidence,
            "source": r.source
        }
        for r in relations
    ]


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: str,
    db: Session = Depends(get_db)
):
    """Delete a relation"""
    
    relation = db.query(models.RegistryRelation).filter_by(id=relation_id).first()
    
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    
    db.delete(relation)
    db.commit()
    
    return {"id": relation_id, "status": "deleted"}


# ========== TREE VIEW ENDPOINT ==========

@router.get("/tree")
async def get_entity_tree(
    project_key: str = Query("default"),
    db: Session = Depends(get_db)
):
    """Get hierarchical tree of entities"""
    
    # Get all root entities (parent_id is None)
    roots = db.query(models.RegistryEntity).filter(
        models.RegistryEntity.project_key == project_key,
        models.RegistryEntity.parent_id.is_(None),
        models.RegistryEntity.status == "active"
    ).all()
    
    tree = []
    for root in roots:
        tree.append(_build_tree_node(root, db))
    
    return {"tree": tree}


def _build_tree_node(entity, db):
    """Build tree node recursively"""
    children = db.query(models.RegistryEntity).filter(
        models.RegistryEntity.parent_id == entity.id,
        models.RegistryEntity.status == "active"
    ).all()
    
    return {
        "id": entity.id,
        "name": entity.canonical_name,
        "type": entity.type,
        "children": [_build_tree_node(child, db) for child in children]
    }


# ========== ENTITY LINKING ENDPOINT ==========

@router.post("/link-mention")
async def link_mention(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Link a text mention to registry entities"""
    
    project_key = request.get("project_key", "default")
    mention_text = request.get("mention_text")
    
    linker = EntityLinker(db, project_key)
    
    scores = linker.link(
        mention_text=mention_text,
        context_text=request.get("context"),
        entity_type_hint=request.get("entity_type"),
        confidence_threshold=request.get("confidence_threshold", 0.5)
    )
    
    best, is_ambiguous = linker.disambiguate(scores)
    
    return {
        "mention": mention_text,
        "candidates": [
            {
                "entity_id": s.registry_entity_id,
                "name": s.canonical_name,
                "score": s.score,
                "signals": s.signals,
                "reasons": s.reasons
            }
            for s in scores[:5]  # Top 5
        ],
        "best_match": {
            "entity_id": best.registry_entity_id,
            "name": best.canonical_name,
            "score": best.score
        } if best else None,
        "is_ambiguous": is_ambiguous
    }


# ========== MERGE ENTITIES ENDPOINT ==========

@router.post("/merge")
async def merge_entities(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Merge duplicate entities"""
    
    from_id = request.get("from_entity_id")
    to_id = request.get("to_entity_id")
    
    from_entity = db.query(models.RegistryEntity).filter_by(id=from_id).first()
    to_entity = db.query(models.RegistryEntity).filter_by(id=to_id).first()
    
    if not from_entity or not to_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Update relations
    relations = db.query(models.RegistryRelation).filter(
        models.RegistryRelation.from_entity_id == from_id
    ).all()
    
    for rel in relations:
        rel.from_entity_id = to_id
    
    # Mark source as deprecated
    from_entity.status = "deprecated"
    from_entity.updated_at = datetime.utcnow()
    
    # Create curation event
    event = models.CurationEvent(
        event_type="ENTITY_MERGE",
        object_id=to_id,
        object_type="registry_entity",
        metadata={
            "merged_ids": [from_id],
            "target_id": to_id,
            "reason": request.get("reason", "duplicate")
        },
        applied=False,
        created_at=datetime.utcnow()
    )
    
    db.add(event)
    db.add(from_entity)
    db.commit()
    
    # Create rule from event
    engine = CurationRulesEngine(db, to_entity.project_key)
    background_tasks.add_task(engine.create_rule_from_event, event.id)
    
    return {
        "from_entity_id": from_id,
        "to_entity_id": to_id,
        "status": "merged",
        "event_id": event.id
    }


# ========== IMPORT ENDPOINT ==========

@router.post("/import")
async def import_entities(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Import entities from CSV/JSON"""
    
    project_key = request.get("project_key", "default")
    entities_data = request.get("entities", [])
    
    imported_ids = []
    
    for entity_data in entities_data:
        # Check uniqueness
        existing = db.query(models.RegistryEntity).filter(
            models.RegistryEntity.project_key == project_key,
            models.RegistryEntity.type == entity_data.get("type"),
            models.RegistryEntity.canonical_name == entity_data.get("canonical_name")
        ).first()
        
        if existing:
            continue  # Skip duplicates
        
        entity = models.RegistryEntity(
            id=str(uuid.uuid4()),
            project_key=project_key,
            entity_key=entity_data.get("entity_key", entity_data.get("canonical_name").lower().replace(" ", "_")),
            type=entity_data.get("type"),
            canonical_name=entity_data.get("canonical_name"),
            aliases=entity_data.get("aliases", []),
            attributes=entity_data.get("attributes", {}),
            description=entity_data.get("description"),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(entity)
        imported_ids.append(entity.id)
    
    db.commit()
    
    return {
        "imported_count": len(imported_ids),
        "entity_ids": imported_ids
    }
