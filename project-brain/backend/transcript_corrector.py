from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models import Lexicon
from logger import get_logger
import difflib

logger = get_logger(__name__)

class TranscriptCorrector:
    """Correct transcript abbreviations and terms based on lexicon"""
    
    @staticmethod
    def correct_transcript(original_text: str, db: Session) -> Dict[str, Any]:
        """
        Correct transcript using lexicon entries.
        Returns corrected text and list of edits with confidence scores.
        """
        logger.info("Starting transcript correction")
        
        # Get all lexicon entries
        lexicon_entries = db.query(Lexicon).all()
        
        corrected_text = original_text
        edits = []
        confidence_threshold = 0.7
        
        # Apply corrections
        for entry in lexicon_entries:
            if entry.category in ["abbreviation", "synonym"]:
                # Check for term and its aliases
                terms_to_check = [entry.term] + entry.aliases
                
                for term in terms_to_check:
                    if term in corrected_text:
                        old_text = corrected_text
                        corrected_text = corrected_text.replace(term, entry.canonical_form)
                        
                        if old_text != corrected_text:
                            edits.append({
                                "original": term,
                                "corrected": entry.canonical_form,
                                "confidence": entry.confidence,
                                "lexicon_id": entry.id
                            })
                            
                            logger.info(f"Corrected: {term} -> {entry.canonical_form}")
        
        # Filter edits by confidence
        high_confidence_edits = [e for e in edits if e["confidence"] >= confidence_threshold]
        
        return {
            "original_text": original_text,
            "corrected_text": corrected_text,
            "edits": high_confidence_edits,
            "correction_status": "completed",
            "total_corrections": len(high_confidence_edits)
        }
    
    @staticmethod
    def generate_diff(original: str, corrected: str) -> List[Dict[str, Any]]:
        """Generate detailed diff between original and corrected text"""
        diffs = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, original, corrected).get_opcodes():
            if tag == "replace":
                diffs.append({
                    "type": "replace",
                    "original": original[i1:i2],
                    "corrected": corrected[j1:j2]
                })
            elif tag == "insert":
                diffs.append({
                    "type": "insert",
                    "text": corrected[j1:j2]
                })
            elif tag == "delete":
                diffs.append({
                    "type": "delete",
                    "text": original[i1:i2]
                })
        return diffs
