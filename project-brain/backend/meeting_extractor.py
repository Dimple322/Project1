from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from models import Issue, ActionItem, Decision, EntityMention, Chunk
from logger import get_logger
import re

logger = get_logger(__name__)

class MeetingExtractor:
    """Extract Issues, Actions, and Decisions from meeting transcripts"""
    
    # Keywords for detection
    ISSUE_KEYWORDS = ["issue", "problem", "concern", "defect", "bug", "failure", "error"]
    ACTION_KEYWORDS = ["action", "todo", "task", "do", "needs", "will", "should"]
    DECISION_KEYWORDS = ["decided", "decision", "agreed", "resolved", "approved"]
    QUESTION_KEYWORDS = ["question", "ask", "what", "how", "why", "when", "where"]
    
    @staticmethod
    def extract_from_transcript(chunk_text: str, chunk_id: str, db: Session) -> Dict[str, Any]:
        """
        Extract issues, actions, decisions, and questions from transcript chunk.
        """
        logger.info(f"Extracting meeting items from chunk: {chunk_id}")
        
        issues = MeetingExtractor._extract_issues(chunk_text, chunk_id)
        actions = MeetingExtractor._extract_actions(chunk_text, chunk_id)
        decisions = MeetingExtractor._extract_decisions(chunk_text, chunk_id)
        questions = MeetingExtractor._extract_questions(chunk_text, chunk_id)
        
        return {
            "issues": issues,
            "actions": actions,
            "decisions": decisions,
            "questions": questions
        }
    
    @staticmethod
    def _extract_issues(text: str, chunk_id: str) -> List[Dict[str, Any]]:
        """Extract issue items from text"""
        issues = []
        
        # Simple pattern-based extraction
        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in MeetingExtractor.ISSUE_KEYWORDS):
                issues.append({
                    "title": sentence[:100],
                    "description": sentence,
                    "status": "open",
                    "priority": "medium",
                    "evidence_chunk_id": chunk_id,
                    "evidence_quote": sentence,
                    "confidence": 0.7,
                    "is_pending_review": True
                })
        
        logger.info(f"Extracted {len(issues)} issues")
        return issues
    
    @staticmethod
    def _extract_actions(text: str, chunk_id: str) -> List[Dict[str, Any]]:
        """Extract action items from text"""
        actions = []
        
        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in MeetingExtractor.ACTION_KEYWORDS):
                actions.append({
                    "title": sentence[:100],
                    "description": sentence,
                    "status": "open",
                    "evidence_chunk_id": chunk_id,
                    "evidence_quote": sentence,
                    "confidence": 0.7,
                    "is_pending_review": True
                })
        
        logger.info(f"Extracted {len(actions)} action items")
        return actions
    
    @staticmethod
    def _extract_decisions(text: str, chunk_id: str) -> List[Dict[str, Any]]:
        """Extract decision items from text"""
        decisions = []
        
        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in MeetingExtractor.DECISION_KEYWORDS):
                decisions.append({
                    "title": sentence[:100],
                    "description": sentence,
                    "evidence_chunk_id": chunk_id,
                    "evidence_quote": sentence,
                    "confidence": 0.8,
                    "is_pending_review": True
                })
        
        logger.info(f"Extracted {len(decisions)} decisions")
        return decisions
    
    @staticmethod
    def _extract_questions(text: str, chunk_id: str) -> List[Dict[str, Any]]:
        """Extract questions from text"""
        questions = []
        
        # Split by question marks and periods
        segments = re.split(r'[?!]', text)
        for segment in segments:
            segment = segment.strip()
            if any(keyword in segment.lower() for keyword in MeetingExtractor.QUESTION_KEYWORDS):
                if segment:
                    questions.append({
                        "text": segment,
                        "chunk_id": chunk_id,
                        "confidence": 0.6,
                        "is_pending_review": True
                    })
        
        logger.info(f"Extracted {len(questions)} questions")
        return questions
