"""
Strong Entity Linking Module (v2)
Disambiguates mentions to registry entities using multiple signals
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import difflib
import re
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class LinkingScore:
    """Result of entity linking"""
    registry_entity_id: str
    canonical_name: str
    score: float
    signals: List[str]
    reasons: List[str]
    confidence: float


class LinkingSignal(Enum):
    """Types of linking signals"""
    EXACT_MATCH = "exact_match"
    ALIAS_MATCH = "alias_match"
    LEXICON_NORMALIZED = "lexicon_normalized"
    FUZZY_MATCH = "fuzzy_match"
    EMBEDDING_SIMILARITY = "embedding_similarity"
    ANCHOR_BIAS = "anchor_bias"
    FREQUENCY_PRIOR = "frequency_prior"
    CONTEXT_MATCH = "context_match"


class EntityLinker:
    """Links mentions to registry entities with scoring"""
    
    def __init__(self, db: Session, project_key: str):
        self.db = db
        self.project_key = project_key
        self._cache = {}
    
    def link(
        self,
        mention_text: str,
        context_text: Optional[str] = None,
        entity_type_hint: Optional[str] = None,
        page_number: Optional[int] = None,
        anchor_entity_id: Optional[str] = None,
        confidence_threshold: float = 0.5
    ) -> List[LinkingScore]:
        """
        Link a mention to registry entities
        
        Args:
            mention_text: The text to link
            context_text: Surrounding context (optional)
            entity_type_hint: Restrict to specific entity type
            page_number: For anchor bias
            anchor_entity_id: Parent entity (for PART_OF bias)
            confidence_threshold: Min confidence to return
        
        Returns:
            Sorted list of LinkingScore candidates
        """
        from models import RegistryEntity, RegistryRelation
        
        # Fetch candidates
        query = self.db.query(RegistryEntity).filter(
            RegistryEntity.project_key == self.project_key,
            RegistryEntity.status == "active"
        )
        
        if entity_type_hint:
            query = query.filter(RegistryEntity.type == entity_type_hint)
        
        candidates = query.all()
        
        if not candidates:
            logger.warning(f"No registry entities found for project {self.project_key}")
            return []
        
        # Score each candidate
        scores = []
        for candidate in candidates:
            score = self._score_candidate(
                mention_text=mention_text,
                context_text=context_text,
                candidate=candidate,
                anchor_entity_id=anchor_entity_id
            )
            
            if score and score.score >= confidence_threshold:
                scores.append(score)
        
        # Sort by score descending
        scores.sort(key=lambda s: s.score, reverse=True)
        
        return scores
    
    def _score_candidate(
        self,
        mention_text: str,
        context_text: Optional[str],
        candidate,
        anchor_entity_id: Optional[str]
    ) -> Optional[LinkingScore]:
        """Score a single candidate"""
        from models import RegistryRelation
        
        scores_dict: Dict[LinkingSignal, float] = {}
        reasons: List[str] = []
        signals: List[str] = []
        
        mention_lower = mention_text.lower().strip()
        candidate_name_lower = candidate.canonical_name.lower()
        
        # Signal 1: Exact match
        if mention_lower == candidate_name_lower:
            scores_dict[LinkingSignal.EXACT_MATCH] = 1.0
            signals.append(LinkingSignal.EXACT_MATCH.value)
            reasons.append(f"Exact match: '{mention_text}' == '{candidate.canonical_name}'")
        
        # Signal 2: Alias match
        if candidate.aliases:
            alias_matches = [a for a in candidate.aliases if a.lower() == mention_lower]
            if alias_matches:
                scores_dict[LinkingSignal.ALIAS_MATCH] = 0.95
                signals.append(LinkingSignal.ALIAS_MATCH.value)
                reasons.append(f"Alias match: '{mention_text}' is alias of '{candidate.canonical_name}'")
        
        # Signal 3: Fuzzy match
        ratio = difflib.SequenceMatcher(None, mention_lower, candidate_name_lower).ratio()
        if ratio > 0.75:
            scores_dict[LinkingSignal.FUZZY_MATCH] = ratio
            signals.append(LinkingSignal.FUZZY_MATCH.value)
            reasons.append(f"Fuzzy match: similarity {ratio:.2f} between '{mention_text}' and '{candidate.canonical_name}'")
        
        # Signal 4: Anchor bias (boost PART_OF relations)
        if anchor_entity_id:
            try:
                parent_relation = self.db.query(RegistryRelation).filter(
                    RegistryRelation.from_entity_id == anchor_entity_id,
                    RegistryRelation.to_entity_id == candidate.id,
                    RegistryRelation.relation_type == "PART_OF"
                ).first()
                
                if parent_relation:
                    scores_dict[LinkingSignal.ANCHOR_BIAS] = 0.3  # Boost
                    signals.append(LinkingSignal.ANCHOR_BIAS.value)
                    reasons.append(f"Anchor bias: entity is PART_OF anchor entity")
            except Exception as e:
                logger.debug(f"Error checking anchor bias: {e}")
        
        # If no signals fired, try substring match (lower confidence)
        if not signals:
            if mention_lower in candidate_name_lower or candidate_name_lower in mention_lower:
                scores_dict[LinkingSignal.CONTEXT_MATCH] = 0.4
                signals.append(LinkingSignal.CONTEXT_MATCH.value)
                reasons.append(f"Partial match: '{mention_text}' contained in or contains '{candidate.canonical_name}'")
        
        if not signals:
            return None
        
        # Aggregate scores (max of all signals)
        final_score = max(scores_dict.values()) if scores_dict else 0.0
        confidence = final_score  # Could be more sophisticated
        
        return LinkingScore(
            registry_entity_id=candidate.id,
            canonical_name=candidate.canonical_name,
            score=final_score,
            signals=signals,
            reasons=reasons,
            confidence=confidence
        )
    
    def disambiguate(
        self,
        scores: List[LinkingScore],
        margin_threshold: float = 0.1
    ) -> Tuple[Optional[LinkingScore], bool]:
        """
        Choose best candidate or flag for review
        
        Returns:
            (best_score, is_ambiguous)
        """
        if not scores:
            return None, False
        
        if len(scores) == 1:
            return scores[0], False
        
        # Check margin between top 2
        if scores[0].score - scores[1].score < margin_threshold:
            logger.warning(f"Ambiguous linking: top scores {scores[0].score:.3f} vs {scores[1].score:.3f}")
            return scores[0], True
        
        return scores[0], False
    
    def build_context_pack(self) -> Dict[str, Any]:
        """
        Build context info from registry, lexicon, and recent claims
        Used for transcript correction and mentions
        """
        from models import RegistryEntity, Lexicon, Claim
        
        context_pack = {
            "entities": {},
            "lexicon": [],
            "recent_claims": {}
        }
        
        # Add all entities with aliases
        entities = self.db.query(RegistryEntity).filter(
            RegistryEntity.project_key == self.project_key,
            RegistryEntity.status == "active"
        ).all()
        
        for entity in entities:
            context_pack["entities"][entity.id] = {
                "name": entity.canonical_name,
                "type": entity.type,
                "aliases": entity.aliases or [],
            }
        
        # Add lexicon
        lexicon_terms = self.db.query(Lexicon).filter(
            Lexicon.confidence >= 0.8
        ).all()
        
        for term in lexicon_terms:
            context_pack["lexicon"].append({
                "term": term.term,
                "canonical": term.canonical_form,
                "category": term.category,
                "aliases": term.aliases or []
            })
        
        return context_pack


class MentionExtractor:
    """Extracts mentions from text"""
    
    @staticmethod
    def extract_mentions(
        text: str,
        registry_entities_dict: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract probable mentions from text
        
        Args:
            text: Source text
            registry_entities_dict: {entity_id: {name, type, aliases}}
        
        Returns:
            List of {mention_text, char_span, entity_candidates}
        """
        mentions = []
        
        # Build pattern from all entity names and aliases
        all_terms = []
        for entity_id, entity_info in registry_entities_dict.items():
            all_terms.append((entity_info["name"], entity_id))
            for alias in entity_info.get("aliases", []):
                all_terms.append((alias, entity_id))
        
        # Sort by length descending (longest match first)
        all_terms.sort(key=lambda t: len(t[0]), reverse=True)
        
        # Simple regex matching
        for term, entity_id in all_terms:
            # Case-insensitive boundary match
            pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                mention = {
                    "text": match.group(),
                    "span": (match.start(), match.end()),
                    "entity_id": entity_id,
                    "confidence": 0.8
                }
                # Check for duplicates (keep longest)
                dup = next((m for m in mentions if m["span"] == mention["span"]), None)
                if not dup:
                    mentions.append(mention)
        
        # Sort by position
        mentions.sort(key=lambda m: m["span"][0])
        
        return mentions
