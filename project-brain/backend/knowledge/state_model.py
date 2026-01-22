"""
Object State Model
Tracks and aggregates current state of project objects
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class StateAggregator:
    """Computes object state from claims, items, and overrides"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compute_state(
        self,
        registry_entity_id: str,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Compute current state of an entity from all evidence
        
        Args:
            registry_entity_id: Entity to compute state for
            as_of_date: Date to compute state as of (default: today)
        
        Returns:
            state_json dict with computed fields
        """
        from models import (
            Claim, Issue, ActionItem, Decision, 
            CurationRule, RegistryEntity
        )
        
        if not as_of_date:
            as_of_date = date.today()
        
        entity = self.db.query(RegistryEntity).filter_by(
            id=registry_entity_id
        ).first()
        
        if not entity:
            raise ValueError(f"Entity not found: {registry_entity_id}")
        
        state = {
            "entity_id": registry_entity_id,
            "entity_name": entity.canonical_name,
            "as_of_date": as_of_date.isoformat(),
            "computed_at": datetime.utcnow().isoformat()
        }
        
        # Collect claims about this entity
        claims = self.db.query(Claim).filter(
            Claim.subject_id == registry_entity_id
        ).all()
        
        # Aggregate claims by field
        state["claims"] = self._aggregate_claims(claims, as_of_date)
        
        # Count issues, actions, decisions
        issues = self.db.query(Issue).filter(
            Issue.subsystem_id == registry_entity_id
        ).all()
        state["open_issues"] = len([i for i in issues if i.status == "open"])
        
        actions = self.db.query(ActionItem).filter(
            ActionItem.assigned_to.isnot(None)  # Simplified
        ).all()
        state["open_actions"] = len([a for a in actions if a.status == "open"])
        
        decisions = self.db.query(Decision).all()
        state["decisions_count"] = len(decisions)
        
        # Apply override rules
        state = self._apply_overrides(state, registry_entity_id)
        
        return state
    
    def _aggregate_claims(
        self,
        claims: List,
        as_of_date: date
    ) -> Dict[str, Any]:
        """Aggregate claims by field with conflict detection"""
        aggregated = {}
        
        # Group by field (from claim text or metadata)
        field_claims = {}
        
        for claim in claims:
            # Extract field from claim metadata or text
            field = claim.metadata.get("field", "general") if hasattr(claim, 'metadata') else "general"
            
            if field not in field_claims:
                field_claims[field] = []
            
            field_claims[field].append({
                "text": claim.claim_text,
                "value": claim.metadata.get("value") if hasattr(claim, 'metadata') else None,
                "confidence": claim.confidence,
                "created_at": claim.created_at
            })
        
        # For each field, choose highest confidence claim
        for field, claims_list in field_claims.items():
            if claims_list:
                # Sort by confidence descending
                claims_list.sort(key=lambda c: c["confidence"], reverse=True)
                top_claim = claims_list[0]
                
                aggregated[field] = {
                    "value": top_claim["value"] or top_claim["text"],
                    "confidence": top_claim["confidence"],
                    "competing_claims": len(claims_list) > 1,
                    "all_claims": claims_list
                }
        
        return aggregated
    
    def _apply_overrides(
        self,
        state: Dict[str, Any],
        registry_entity_id: str
    ) -> Dict[str, Any]:
        """Apply claim override rules to state"""
        from models import CurationRule
        
        # Get override rules
        rules = self.db.query(CurationRule).filter(
            CurationRule.rule_type == "CLAIM_OVERRIDE_RULE"
        ).all()
        
        for rule in rules:
            payload = rule.payload or {}
            field = payload.get("field")
            new_value = payload.get("new_value")
            
            if field and field in state.get("claims", {}):
                state["claims"][field]["override"] = {
                    "value": new_value,
                    "rule_id": rule.id,
                    "reason": payload.get("reason", "manual override")
                }
        
        return state
    
    def save_state(
        self,
        registry_entity_id: str,
        state_json: Dict[str, Any],
        as_of_date: Optional[date] = None
    ) -> str:
        """Save computed state to database"""
        from models import ObjectState
        
        if not as_of_date:
            as_of_date = date.today()
        
        # Check for existing state on this date
        existing = self.db.query(ObjectState).filter(
            ObjectState.registry_entity_id == registry_entity_id,
            ObjectState.as_of_date == as_of_date
        ).first()
        
        if existing:
            existing.state_json = state_json
            existing.created_at = datetime.utcnow()
            self.db.add(existing)
        else:
            state_obj = ObjectState(
                registry_entity_id=registry_entity_id,
                as_of_date=as_of_date,
                state_json=state_json,
                confidence=0.85,
                created_at=datetime.utcnow()
            )
            self.db.add(state_obj)
        
        self.db.commit()
        
        return existing.id if existing else state_obj.id
    
    def detect_conflicts(
        self,
        registry_entity_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicting claims about an entity
        Returns list of conflicts
        """
        from models import Claim, StateConflict
        
        state = self.compute_state(registry_entity_id)
        conflicts = []
        
        for field, claim_info in state.get("claims", {}).items():
            if claim_info.get("competing_claims"):
                claim_list = claim_info.get("all_claims", [])
                if len(claim_list) > 1:
                    # Extract distinct values
                    values = list(set(
                        c.get("value") or c.get("text") for c in claim_list
                    ))
                    
                    if len(values) > 1:
                        conflict = {
                            "registry_entity_id": registry_entity_id,
                            "field_path": field,
                            "competing_values": values,
                            "claim_count": len(claim_list),
                            "status": "open"
                        }
                        conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflict(
        self,
        registry_entity_id: str,
        field_path: str,
        chosen_value: Any,
        reason: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Resolve a state conflict
        Creates a claim override rule and curation event
        """
        from models import StateConflict, CurationEvent, CurationRule
        
        # Find and update conflict record
        conflict = self.db.query(StateConflict).filter(
            StateConflict.registry_entity_id == registry_entity_id,
            StateConflict.field_path == field_path,
            StateConflict.status == "open"
        ).first()
        
        if not conflict:
            raise ValueError(f"No open conflict found for {field_path}")
        
        # Create override rule
        rule = CurationRule(
            project_key="default",  # TODO: get from entity
            rule_type="CLAIM_OVERRIDE_RULE",
            payload={
                "field": field_path,
                "new_value": chosen_value,
                "reason": reason,
                "scope": "entity"
            },
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(rule)
        self.db.flush()
        
        # Create curation event
        event = CurationEvent(
            event_type="CLAIM_OVERRIDE",
            object_id=registry_entity_id,
            object_type="registry_entity",
            metadata={
                "field": field_path,
                "chosen_value": str(chosen_value),
                "reason": reason
            },
            applied=False,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.flush()
        
        # Mark conflict as resolved
        conflict.status = "resolved"
        conflict.resolution_event_id = event.id
        conflict.updated_at = datetime.utcnow()
        
        self.db.add(conflict)
        self.db.commit()
        
        logger.info(f"Resolved conflict for {field_path}: chose {chosen_value}")
        
        return event.id


class StateReportBuilder:
    """Builds comprehensive status reports from object state"""
    
    def __init__(self, db: Session):
        self.db = db
        self.aggregator = StateAggregator(db)
    
    def build_status_report(
        self,
        registry_entity_id: str,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Build comprehensive status report for an object"""
        from models import RegistryEntity
        
        entity = self.db.query(RegistryEntity).filter_by(
            id=registry_entity_id
        ).first()
        
        if not entity:
            raise ValueError(f"Entity not found: {registry_entity_id}")
        
        state = self.aggregator.compute_state(registry_entity_id, as_of_date)
        conflicts = self.aggregator.detect_conflicts(registry_entity_id)
        
        report = {
            "entity_id": registry_entity_id,
            "entity_name": entity.canonical_name,
            "entity_type": entity.type,
            "as_of_date": (as_of_date or date.today()).isoformat(),
            "state": state,
            "conflicts": conflicts,
            "summary": self._build_summary(state, conflicts),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return report
    
    def _build_summary(
        self,
        state: Dict[str, Any],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build executive summary"""
        return {
            "total_claims": len(state.get("claims", {})),
            "open_issues": state.get("open_issues", 0),
            "open_actions": state.get("open_actions", 0),
            "decisions": state.get("decisions_count", 0),
            "conflicts_count": len(conflicts),
            "health_score": self._compute_health(state, conflicts)
        }
    
    def _compute_health(
        self,
        state: Dict[str, Any],
        conflicts: List[Dict[str, Any]]
    ) -> float:
        """Compute health score 0-1"""
        score = 0.5  # Start at 50%
        
        # Reduce for issues and actions
        score -= state.get("open_issues", 0) * 0.05
        score -= state.get("open_actions", 0) * 0.03
        
        # Reduce for conflicts
        score -= len(conflicts) * 0.1
        
        # Boost for decisions
        score += state.get("decisions_count", 0) * 0.02
        
        # Clamp 0-1
        return max(0.0, min(1.0, score))
