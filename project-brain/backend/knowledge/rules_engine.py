"""
Curation Rules Engine
Applies learned rules to parsing, linking, and correction pipelines
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RuleType(Enum):
    LINK_FIX_RULE = "LINK_FIX_RULE"
    PARSING_ANCHOR_RULE = "PARSING_ANCHOR_RULE"
    LEXICON_NORMALIZATION_RULE = "LEXICON_NORMALIZATION_RULE"
    CLAIM_OVERRIDE_RULE = "CLAIM_OVERRIDE_RULE"
    PARSING_RULE = "PARSING_RULE"


@dataclass
class RuleApplication:
    """Result of applying a rule"""
    rule_id: str
    rule_type: RuleType
    matched: bool
    output: Any
    reason: str


class CurationRulesEngine:
    """Applies learned curation rules"""
    
    def __init__(self, db: Session, project_key: str):
        self.db = db
        self.project_key = project_key
    
    def create_rule_from_event(self, event_id: str) -> Optional[str]:
        """
        Convert a curation event into a rule
        Returns rule_id if created
        """
        from models import CurationEvent, CurationRule
        
        event = self.db.query(CurationEvent).filter_by(id=event_id).first()
        if not event:
            return None
        
        rule_payload = self._convert_event_to_rule_payload(event)
        if not rule_payload:
            return None
        
        rule_type_str = self._infer_rule_type(event.event_type)
        
        rule = CurationRule(
            project_key=self.project_key,
            rule_type=rule_type_str,
            payload=rule_payload,
            priority=50,  # Default priority
            enabled=True,
            created_from_event_id=event_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(rule)
        self.db.commit()
        
        logger.info(f"Created rule from event {event_id}: {rule.id}")
        return rule.id
    
    def _convert_event_to_rule_payload(self, event) -> Optional[Dict[str, Any]]:
        """Convert specific curation event to rule payload"""
        metadata = event.metadata or {}
        
        if event.event_type == "LINK_FIX":
            # Example: {mention_text, entity_id, context_patterns}
            return {
                "type": "LINK_FIX_RULE",
                "mention_pattern": metadata.get("mention_text"),
                "entity_id": metadata.get("entity_id"),
                "confidence": 0.9
            }
        
        elif event.event_type == "ENTITY_MERGE":
            return {
                "type": "LINK_FIX_RULE",
                "merge_from_ids": metadata.get("merged_ids"),
                "merge_to_id": metadata.get("target_id")
            }
        
        elif event.event_type == "LEXICON_ADD":
            return {
                "type": "LEXICON_NORMALIZATION_RULE",
                "term": metadata.get("term"),
                "canonical_form": metadata.get("canonical_form"),
                "category": metadata.get("category")
            }
        
        elif event.event_type == "CLAIM_OVERRIDE":
            return {
                "type": "CLAIM_OVERRIDE_RULE",
                "field": metadata.get("field"),
                "new_value": metadata.get("new_value"),
                "scope": metadata.get("scope")
            }
        
        return None
    
    def _infer_rule_type(self, event_type: str) -> str:
        mapping = {
            "LINK_FIX": "LINK_FIX_RULE",
            "ENTITY_MERGE": "LINK_FIX_RULE",
            "LEXICON_ADD": "LEXICON_NORMALIZATION_RULE",
            "CLAIM_OVERRIDE": "CLAIM_OVERRIDE_RULE",
            "PARSING_RULE_ADD": "PARSING_RULE"
        }
        return mapping.get(event_type, "PARSING_RULE")
    
    def get_applicable_rules(self, rule_type: RuleType) -> List:
        """Get all enabled rules of a specific type"""
        from models import CurationRule
        
        return self.db.query(CurationRule).filter(
            CurationRule.project_key == self.project_key,
            CurationRule.rule_type == rule_type.value,
            CurationRule.enabled == True
        ).order_by(CurationRule.priority.desc()).all()
    
    def apply_link_fix_rules(
        self,
        mention_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[RuleApplication]:
        """Apply link fix rules to a mention"""
        from models import CurationRule
        
        rules = self.get_applicable_rules(RuleType.LINK_FIX_RULE)
        applications = []
        
        for rule in rules:
            payload = rule.payload
            
            # Check if mention matches pattern
            pattern = payload.get("mention_pattern", "").lower()
            mention_lower = mention_text.lower()
            
            if pattern in mention_lower or mention_lower in pattern:
                app = RuleApplication(
                    rule_id=rule.id,
                    rule_type=RuleType.LINK_FIX_RULE,
                    matched=True,
                    output={"entity_id": payload.get("entity_id")},
                    reason=f"Link fix rule matched pattern '{pattern}'"
                )
                applications.append(app)
        
        return applications
    
    def apply_normalization_rules(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Apply lexicon normalization rules"""
        from models import CurationRule
        
        rules = self.get_applicable_rules(RuleType.LEXICON_NORMALIZATION_RULE)
        corrections = []
        
        result_text = text
        
        for rule in rules:
            payload = rule.payload
            term = payload.get("term", "").lower()
            canonical = payload.get("canonical_form", "")
            
            if term in result_text.lower():
                # Simple case-insensitive replacement
                import re
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                matches = list(pattern.finditer(result_text))
                
                for match in matches:
                    corrections.append({
                        "original": match.group(),
                        "corrected": canonical,
                        "char_span": match.span(),
                        "confidence": payload.get("confidence", 0.9),
                        "rule_id": rule.id
                    })
                
                result_text = pattern.sub(canonical, result_text)
        
        return {
            "corrected_text": result_text,
            "corrections": corrections
        }
    
    def apply_claim_override_rules(
        self,
        entity_id: str,
        field_name: str,
        current_value: Any
    ) -> Optional[Dict[str, Any]]:
        """Check if there's a claim override rule for this field"""
        from models import CurationRule
        
        rules = self.get_applicable_rules(RuleType.CLAIM_OVERRIDE_RULE)
        
        for rule in rules:
            payload = rule.payload
            if payload.get("field") == field_name:
                return {
                    "new_value": payload.get("new_value"),
                    "reason": payload.get("scope", "manual override"),
                    "rule_id": rule.id,
                    "confidence": 0.95
                }
        
        return None
    
    def test_rule(
        self,
        rule_id: str,
        test_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a rule with sample input"""
        from models import CurationRule
        
        rule = self.db.query(CurationRule).filter_by(id=rule_id).first()
        if not rule:
            return {"error": "Rule not found"}
        
        rule_type = RuleType(rule.rule_type)
        
        if rule_type == RuleType.LINK_FIX_RULE:
            apps = self.apply_link_fix_rules(test_input.get("mention", ""))
            return {
                "rule_id": rule_id,
                "applied": len(apps) > 0,
                "matches": [a.to_dict() for a in apps]
            }
        
        elif rule_type == RuleType.LEXICON_NORMALIZATION_RULE:
            result = self.apply_normalization_rules(test_input.get("text", ""))
            return {
                "rule_id": rule_id,
                "applied": len(result["corrections"]) > 0,
                "corrections": result["corrections"]
            }
        
        return {"error": "Unsupported rule type for testing"}


class RulePipeline:
    """Pipeline that applies multiple rule types in sequence"""
    
    def __init__(self, engine: CurationRulesEngine):
        self.engine = engine
    
    def process_mention(
        self,
        mention_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a mention through all applicable rules
        """
        result = {
            "original_mention": mention_text,
            "final_mention": mention_text,
            "rules_applied": [],
            "is_corrected": False
        }
        
        # Apply link fix rules (may provide direct entity_id)
        link_fixes = self.engine.apply_link_fix_rules(mention_text, context)
        if link_fixes and link_fixes[0].matched:
            result["rules_applied"].append(link_fixes[0].__dict__)
            result["entity_id"] = link_fixes[0].output.get("entity_id")
        
        return result
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text through normalization rules
        """
        result = self.engine.apply_normalization_rules(text)
        return {
            "original": text,
            "corrected": result["corrected_text"],
            "corrections": result["corrections"],
            "is_corrected": len(result["corrections"]) > 0
        }
