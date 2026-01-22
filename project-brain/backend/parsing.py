from typing import Optional, List
import json
import requests
from logger import get_logger
from config import settings

logger = get_logger(__name__)

class DocumentParser:
    """Parse documents using Docling (primary) or Unstructured (fallback)"""
    
    @staticmethod
    def parse_pdf(file_path: str) -> dict:
        """Parse PDF using Docling"""
        try:
            from docling.document_converter import DocumentConverter
            
            converter = DocumentConverter()
            result = converter.convert(file_path)
            
            chunks = []
            for i, page in enumerate(result.pages, 1):
                text = page.export_to_markdown()
                chunks.append({
                    "page_number": i,
                    "section_path": None,
                    "text": text
                })
            
            return {
                "status": "success",
                "chunks": chunks,
                "page_count": len(result.pages),
                "parser": "docling"
            }
        except Exception as e:
            logger.warning(f"Docling failed for {file_path}: {e}")
            return DocumentParser._parse_pdf_unstructured(file_path)
    
    @staticmethod
    def _parse_pdf_unstructured(file_path: str) -> dict:
        """Fallback: Parse PDF using Unstructured"""
        try:
            from unstructured.partition.pdf import partition_pdf
            
            elements = partition_pdf(file_path)
            
            chunks = []
            for i, element in enumerate(elements):
                text = str(element)
                if text.strip():
                    chunks.append({
                        "page_number": getattr(element, "metadata", {}).get("page_number"),
                        "section_path": None,
                        "text": text
                    })
            
            return {
                "status": "success",
                "chunks": chunks,
                "parser": "unstructured"
            }
        except Exception as e:
            logger.error(f"Unstructured failed for {file_path}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "parser": "unstructured"
            }
    
    @staticmethod
    def parse_docx(file_path: str) -> dict:
        """Parse DOCX file"""
        try:
            from unstructured.partition.docx import partition_docx
            
            elements = partition_docx(file_path)
            
            chunks = []
            current_section = None
            for element in elements:
                text = str(element)
                if text.strip():
                    if hasattr(element, "metadata") and element.metadata.get("category") == "Header":
                        current_section = text
                    chunks.append({
                        "page_number": None,
                        "section_path": current_section,
                        "text": text
                    })
            
            return {
                "status": "success",
                "chunks": chunks,
                "parser": "unstructured"
            }
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "parser": "unstructured"
            }
    
    @staticmethod
    def parse_file(file_path: str, mime_type: str) -> dict:
        """Parse file based on MIME type"""
        logger.info(f"Parsing file: {file_path} (MIME: {mime_type})")
        
        if mime_type == "application/pdf":
            return DocumentParser.parse_pdf(file_path)
        elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return DocumentParser.parse_docx(file_path)
        elif mime_type in ["text/plain"]:
            return DocumentParser._parse_text_file(file_path)
        else:
            return {
                "status": "failed",
                "error": f"Unsupported MIME type: {mime_type}",
                "parser": "unknown"
            }
    
    @staticmethod
    def _parse_text_file(file_path: str) -> dict:
        """Parse plain text file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            chunks = []
            lines = text.split("\n\n")
            for i, chunk in enumerate(lines):
                if chunk.strip():
                    chunks.append({
                        "page_number": None,
                        "section_path": None,
                        "text": chunk
                    })
            
            return {
                "status": "success",
                "chunks": chunks,
                "parser": "text"
            }
        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "parser": "text"
            }
