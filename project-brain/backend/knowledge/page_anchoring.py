"""
PDF Page Anchoring Module
Detects objects on pages and attaches tables/sections to them
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import re

logger = logging.getLogger(__name__)


class AnchorDetector:
    """Detects anchors (object names) on PDF pages"""
    
    def __init__(self, db: Session, project_key: str):
        self.db = db
        self.project_key = project_key
    
    def detect_anchors(
        self,
        doc_version_id: str,
        page_number: int,
        page_text: str,
        blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect anchors (object references) on a page
        
        Args:
            doc_version_id: Document version ID
            page_number: Page number
            page_text: Full page text
            blocks: List of page blocks with text/bbox
        
        Returns:
            List of {anchor_text, bbox, registry_entity_id, confidence, source}
        """
        from models import RegistryEntity, PageAnchor
        
        anchors = []
        
        # Get all registry entities for this project
        entities = self.db.query(RegistryEntity).filter(
            RegistryEntity.project_key == self.project_key,
            RegistryEntity.status == "active"
        ).all()
        
        if not entities:
            logger.warning(f"No registry entities found for project {self.project_key}")
            return []
        
        # Build searchable terms (name + aliases)
        search_terms = {}
        for entity in entities:
            search_terms[entity.canonical_name.lower()] = entity.id
            for alias in (entity.aliases or []):
                search_terms[alias.lower()] = entity.id
        
        # Search for matches in page text
        # Look for headings or text blocks that match entity names
        found_anchors = set()
        
        for term, entity_id in search_terms.items():
            # Find positions in page text
            term_lower = term.lower()
            page_text_lower = page_text.lower()
            
            # Use word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            matches = list(re.finditer(pattern, page_text_lower))
            
            for match in matches:
                anchor_text = page_text[match.start():match.end()]
                
                # Find which block contains this match
                block_bbox = self._find_block_for_position(
                    match.start(),
                    page_text,
                    blocks,
                    page_number
                )
                
                # Avoid duplicates
                anchor_key = (anchor_text.lower(), entity_id)
                if anchor_key not in found_anchors:
                    found_anchors.add(anchor_key)
                    
                    anchors.append({
                        "anchor_text": anchor_text,
                        "bbox": block_bbox,
                        "registry_entity_id": entity_id,
                        "confidence": 0.95,
                        "source": "regex",
                        "detection_method": "entity_name_match"
                    })
        
        # If no anchors found, try OCR-based detection (placeholder)
        if not anchors:
            logger.debug(f"No anchors detected on page {page_number}")
        
        return anchors
    
    def _find_block_for_position(
        self,
        char_position: int,
        page_text: str,
        blocks: List[Dict[str, Any]],
        page_number: int
    ) -> Optional[Dict[str, float]]:
        """Find bbox for a character position in page text"""
        # Simplified: just return approximate bbox
        # In production, would use precise text positioning from Docling
        return {
            "x0": 50,
            "y0": 50,
            "x1": 500,
            "y1": 100,
            "page": page_number
        }


class TableAttachmentService:
    """Manages attachment of tables to objects"""
    
    def __init__(self, db: Session, project_key: str):
        self.db = db
        self.project_key = project_key
    
    def attach_table_to_anchor(
        self,
        doc_version_id: str,
        page_number: int,
        block_id: str,
        anchor_id: str,
        registry_entity_id: str,
        confidence: float = 0.9,
        source: str = "system"
    ) -> str:
        """Attach a table block to an entity via an anchor"""
        from models import TableAttachment
        
        attachment = TableAttachment(
            doc_version_id=doc_version_id,
            page_number=page_number,
            block_id=block_id,
            registry_entity_id=registry_entity_id,
            confidence=confidence,
            anchor_id=anchor_id,
            source=source,
            created_at=datetime.utcnow()
        )
        
        self.db.add(attachment)
        self.db.commit()
        
        logger.info(f"Attached table {block_id} to entity {registry_entity_id}")
        return attachment.id
    
    def auto_attach_tables(
        self,
        doc_version_id: str,
        page_number: int,
        blocks: List[Dict[str, Any]],
        anchors: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Automatically attach table blocks to anchors based on proximity
        
        Args:
            doc_version_id: Document version
            page_number: Current page
            blocks: Page blocks (with type=table)
            anchors: Detected anchors on page
        
        Returns:
            List of attachment IDs
        """
        from models import DocPageBlock, PageAnchor, TableAttachment
        
        attachment_ids = []
        
        # Save anchors first
        for anchor_info in anchors:
            existing_anchor = self.db.query(PageAnchor).filter(
                PageAnchor.doc_version_id == doc_version_id,
                PageAnchor.page_number == page_number,
                PageAnchor.anchor_text == anchor_info["anchor_text"]
            ).first()
            
            if not existing_anchor:
                anchor = PageAnchor(
                    doc_version_id=doc_version_id,
                    page_number=page_number,
                    anchor_text=anchor_info["anchor_text"],
                    bbox=anchor_info.get("bbox"),
                    registry_entity_id=anchor_info.get("registry_entity_id"),
                    confidence=anchor_info.get("confidence", 0.95),
                    source=anchor_info.get("source", "system"),
                    detection_method=anchor_info.get("detection_method"),
                    created_at=datetime.utcnow()
                )
                self.db.add(anchor)
                self.db.flush()
            else:
                anchor = existing_anchor
        
        self.db.commit()
        
        # Attach tables to nearest anchors
        for block in blocks:
            if block.get("type") != "table":
                continue
            
            block_id = block.get("id")
            if not block_id:
                continue
            
            # Find nearest anchor by position
            nearest_anchor = self._find_nearest_anchor(block, anchors)
            
            if nearest_anchor:
                attachment = TableAttachment(
                    doc_version_id=doc_version_id,
                    page_number=page_number,
                    block_id=block_id,
                    registry_entity_id=nearest_anchor["registry_entity_id"],
                    confidence=0.85,
                    anchor_id=nearest_anchor.get("id"),
                    source="system",
                    created_at=datetime.utcnow()
                )
                self.db.add(attachment)
                attachment_ids.append(attachment.id)
        
        self.db.commit()
        
        return attachment_ids
    
    def _find_nearest_anchor(
        self,
        block: Dict[str, Any],
        anchors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find nearest anchor above a block"""
        if not anchors:
            return None
        
        # Simple heuristic: anchor above block (in reading order)
        block_y = block.get("bbox", {}).get("y0", float('inf'))
        
        candidates = [a for a in anchors if a.get("bbox", {}).get("y0", 0) < block_y]
        
        if candidates:
            # Return the closest one (lowest y value)
            return min(candidates, key=lambda a: abs(a.get("bbox", {}).get("y0", 0) - block_y))
        
        # If no anchor above, return first anchor
        return anchors[0] if anchors else None
    
    def manual_attachment(
        self,
        table_attachment_id: str,
        new_registry_entity_id: str,
        user_id: str
    ) -> str:
        """
        Manually reassign a table attachment
        Creates curation event
        """
        from models import TableAttachment, CurationEvent
        
        attachment = self.db.query(TableAttachment).filter_by(
            id=table_attachment_id
        ).first()
        
        if not attachment:
            raise ValueError(f"Attachment not found: {table_attachment_id}")
        
        old_entity_id = attachment.registry_entity_id
        attachment.registry_entity_id = new_registry_entity_id
        attachment.source = "manual"
        attachment.created_at = datetime.utcnow()
        
        self.db.add(attachment)
        self.db.flush()
        
        # Create curation event
        event = CurationEvent(
            event_type="PARSING_ANCHOR_RULE",
            object_id=table_attachment_id,
            object_type="table_attachment",
            metadata={
                "old_entity_id": old_entity_id,
                "new_entity_id": new_registry_entity_id,
                "action": "manual_reassignment"
            },
            applied=False,
            created_at=datetime.utcnow()
        )
        
        self.db.add(event)
        self.db.commit()
        
        logger.info(f"Manual attachment reassignment: {old_entity_id} -> {new_registry_entity_id}")
        return event.id


class PageStructureParser:
    """Parses PDF page structure (blocks, bbox, etc.)"""
    
    @staticmethod
    def extract_blocks_from_docling(docling_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract page blocks from Docling output
        
        Docling provides rich block-level info with bbox
        """
        blocks = []
        
        pages = docling_output.get("pages", [])
        for page_idx, page in enumerate(pages):
            page_blocks = page.get("blocks", [])
            
            for block_idx, block in enumerate(page_blocks):
                block_type = block.get("type", "text")  # text, table, figure, list
                bbox = block.get("bbox")  # {x0, y0, x1, y1}
                text = block.get("text", "")
                
                blocks.append({
                    "id": f"block_{page_idx}_{block_idx}",
                    "page": page_idx + 1,
                    "type": block_type,
                    "text": text,
                    "bbox": bbox,
                    "metadata": {
                        "docling_type": block_type,
                        "original_index": block_idx
                    }
                })
        
        return blocks
    
    @staticmethod
    def extract_blocks_fallback(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback block extraction from existing chunks
        (when bbox not available)
        """
        blocks = []
        
        for chunk in chunks:
            block = {
                "id": chunk.get("id"),
                "page": chunk.get("page_number"),
                "type": "text",  # Unknown type
                "text": chunk.get("text_content", ""),
                "bbox": None,
                "metadata": {}
            }
            blocks.append(block)
        
        return blocks
