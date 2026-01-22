"""
Object State and Rules Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import uuid
import logging

from db import get_db
import models
from knowledge.state_model import StateAggregator, StateReportBuilder
from knowledge.rules_engine import CurationRulesEngine, RuleType

logger = logging.getLogger(__name__)

state_router = APIRouter(prefix="/state", tags=["state"])
rules_router = APIRouter(prefix="/rules", tags=["rules"])


# ========== STATE ENDPOINTS ==========

@state_router.post("/compute")
async def compute_object_state(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Compute state of an object from claims"""
    
    entity_id = request.get("registry_entity_id")
    as_of_date = request.get("as_of_date")
    
    if as_of_date:
        as_of_date = datetime.fromisoformat(as_of_date).date()
    
    aggregator = StateAggregator(db)
    
    try:
        state = aggregator.compute_state(entity_id, as_of_date)
        state_id = aggregator.save_state(entity_id, state, as_of_date)
        
        return {
            "state_id": state_id,
            "entity_id": entity_id,
            "state": state,
            "status": "computed"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@state_router.get("/entity/{entity_id}")
async def get_entity_state(
    entity_id: str,
    as_of_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get latest state of an entity"""
    
    query = db.query(models.ObjectState).filter(
        models.ObjectState.registry_entity_id == entity_id
    ).order_by(models.ObjectState.as_of_date.desc())
    
    if as_of_date:
        target_date = datetime.fromisoformat(as_of_date).date()
        query = query.filter(models.ObjectState.as_of_date <= target_date)
    
    state_obj = query.first()
    
    if not state_obj:
        raise HTTPException(status_code=404, detail="No state found")
    
    return {
        "entity_id": entity_id,
        "as_of_date": state_obj.as_of_date.isoformat(),
        "state": state_obj.state_json,
        "computed_from": state_obj.computed_from,
        "confidence": state_obj.confidence
    }


@state_router.get("/conflicts/{entity_id}")
async def get_conflicts(
    entity_id: str,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get state conflicts for an entity"""
    
    query = db.query(models.StateConflict).filter(
        models.StateConflict.registry_entity_id == entity_id
    )
    
    if status:
        query = query.filter(models.StateConflict.status == status)
    
    conflicts = query.all()
    
    return {
        "entity_id": entity_id,
        "conflicts": [
            {
                "id": c.id,
                "field_path": c.field_path,
                "competing_values": c.conflict_values,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            }
            for c in conflicts
        ]
    }


@state_router.post("/conflicts/{entity_id}/resolve")
async def resolve_conflict(
    entity_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Resolve a state conflict"""
    
    field_path = request.get("field_path")
    chosen_value = request.get("chosen_value")
    reason = request.get("reason")
    user_id = request.get("user_id", "system")
    
    aggregator = StateAggregator(db)
    
    try:
        event_id = aggregator.resolve_conflict(
            registry_entity_id=entity_id,
            field_path=field_path,
            chosen_value=chosen_value,
            reason=reason,
            user_id=user_id
        )
        
        return {
            "entity_id": entity_id,
            "field_path": field_path,
            "event_id": event_id,
            "status": "resolved"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@state_router.post("/report/{entity_id}")
async def generate_status_report(
    entity_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate comprehensive status report"""
    
    as_of_date = request.get("as_of_date")
    
    if as_of_date:
        as_of_date = datetime.fromisoformat(as_of_date).date()
    
    builder = StateReportBuilder(db)
    
    try:
        report = builder.build_status_report(entity_id, as_of_date)
        
        return {
            "entity_id": entity_id,
            "report": report,
            "status": "generated"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== RULES ENDPOINTS ==========

@rules_router.post("/create-from-event")
async def create_rule_from_event(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a rule from a curation event"""
    
    event_id = request.get("event_id")
    project_key = request.get("project_key", "default")
    
    engine = CurationRulesEngine(db, project_key)
    
    try:
        rule_id = engine.create_rule_from_event(event_id)
        
        if not rule_id:
            raise ValueError("Could not create rule from event")
        
        return {
            "event_id": event_id,
            "rule_id": rule_id,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rules_router.get("/")
async def list_rules(
    project_key: str = Query("default"),
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List curation rules"""
    
    query = db.query(models.CurationRule).filter(
        models.CurationRule.project_key == project_key
    )
    
    if rule_type:
        query = query.filter(models.CurationRule.rule_type == rule_type)
    
    if enabled is not None:
        query = query.filter(models.CurationRule.enabled == enabled)
    
    rules = query.order_by(models.CurationRule.priority.desc()).all()
    
    return {
        "count": len(rules),
        "rules": [
            {
                "id": r.id,
                "rule_type": r.rule_type,
                "priority": r.priority,
                "enabled": r.enabled,
                "created_from_event_id": r.created_from_event_id,
                "created_at": r.created_at.isoformat()
            }
            for r in rules
        ]
    }


@rules_router.get("/{rule_id}")
async def get_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Get rule details"""
    
    rule = db.query(models.CurationRule).filter_by(id=rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "id": rule.id,
        "rule_type": rule.rule_type,
        "payload": rule.payload,
        "priority": rule.priority,
        "enabled": rule.enabled,
        "test_cases": rule.test_cases,
        "created_at": rule.created_at.isoformat()
    }


@rules_router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update rule (priority, enabled, etc.)"""
    
    rule = db.query(models.CurationRule).filter_by(id=rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    if "priority" in request:
        rule.priority = request["priority"]
    if "enabled" in request:
        rule.enabled = request["enabled"]
    if "payload" in request:
        rule.payload = request["payload"]
    
    rule.updated_at = datetime.utcnow()
    db.add(rule)
    db.commit()
    
    return {"id": rule.id, "status": "updated"}


@rules_router.post("/{rule_id}/test")
async def test_rule(
    rule_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Test a rule with sample input"""
    
    project_key = request.get("project_key", "default")
    test_input = request.get("test_input", {})
    
    engine = CurationRulesEngine(db, project_key)
    
    result = engine.test_rule(rule_id, test_input)
    
    return result


@rules_router.post("/{rule_id}/test-cases/add")
async def add_test_case(
    rule_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Add test case to rule"""
    
    rule = db.query(models.CurationRule).filter_by(id=rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    test_case = {
        "input": request.get("input"),
        "expected_output": request.get("expected_output"),
        "description": request.get("description")
    }
    
    if not rule.test_cases:
        rule.test_cases = []
    
    rule.test_cases.append(test_case)
    rule.updated_at = datetime.utcnow()
    
    db.add(rule)
    db.commit()
    
    return {
        "rule_id": rule_id,
        "test_case_added": True,
        "total_test_cases": len(rule.test_cases)
    }


@rules_router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Delete a rule"""
    
    rule = db.query(models.CurationRule).filter_by(id=rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    
    return {"id": rule_id, "status": "deleted"}
