"""
LLM client for LM Studio with OpenAI-compatible API
"""
import os
from typing import Optional, List
from logger import get_logger

logger = get_logger(__name__)

class LLMClient:
    """OpenAI-compatible LLM client for LM Studio"""
    
    def __init__(self):
        self.base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234") + "/v1"
        self.model = os.getenv("LM_STUDIO_MODEL", "mistralai/ministral-3-14b-reasoning")
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=self.base_url,
                api_key="lm-studio"  # LM Studio doesn't require real key
            )
            logger.info(f"? LLM Client initialized: {self.base_url} (model: {self.model})")
        except Exception as e:
            logger.warning(f"? LLM Client init failed: {e}. LLM features will be unavailable.")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self.client is not None
    
    def answer(self, question: str, context: str = "", system_prompt: str = None) -> Optional[str]:
        """
        Generate answer using LLM with optional context (RAG)
        
        Args:
            question: The question to answer
            context: Optional context/documents for RAG
            system_prompt: Optional custom system prompt
            
        Returns:
            The LLM's answer or None if LLM unavailable
        """
        if not self.is_available():
            logger.warning("LLM not available, returning None")
            return None
        
        try:
            # Build prompt
            if context:
                prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:"""
            else:
                prompt = f"Question: {question}\n\nAnswer:"
            
            # System prompt
            if not system_prompt:
                system_prompt = "You are a helpful assistant that answers questions accurately and concisely."
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512,
                top_p=0.9,
            )
            
            answer = response.choices[0].message.content
            logger.info(f"? LLM answered question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None
    
    def extract_entities(self, text: str) -> Optional[List[dict]]:
        """Extract entities from text using LLM"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract entities (names, organizations, locations, etc.) from the given text. Return as JSON array of objects with 'entity' and 'type' fields."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=256,
            )
            
            answer = response.choices[0].message.content
            
            # Try to parse JSON
            import json
            try:
                entities = json.loads(answer)
                return entities if isinstance(entities, list) else []
            except:
                logger.warning(f"Could not parse LLM entity response as JSON: {answer}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return None


# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
