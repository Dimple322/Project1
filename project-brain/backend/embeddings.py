import json
from typing import List, Dict, Optional
import numpy as np
from scipy.spatial.distance import cosine
from logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    """Local embedding service using bge-m3 model"""
    
    def __init__(self):
        try:
            from FlagEmbedding import BGEM3FlagModel
            self.model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
            logger.info("Loaded BGE-M3 model for embeddings")
        except ImportError:
            logger.warning("BGE-M3 not available, using mock embeddings")
            self.model = None
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if self.model is None:
            return self._mock_embedding(text)
        
        try:
            result = self.model.encode([text])
            embeddings = result['dense_vecs']
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return self._mock_embedding(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.model is None:
            return [self._mock_embedding(text) for text in texts]
        
        try:
            result = self.model.encode(texts)
            embeddings = result['dense_vecs']
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            return [self._mock_embedding(text) for text in texts]
    
    @staticmethod
    def _mock_embedding(text: str) -> List[float]:
        """Generate mock embedding for development"""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % (2**32)
        np.random.seed(seed)
        return np.random.normal(0, 1, 1024).tolist()

class RerankerService:
    """Rerank search results using bge-reranker-v2-m3"""
    
    def __init__(self):
        try:
            from FlagEmbedding import FlagReranker
            self.reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
            logger.info("Loaded BGE-Reranker-v2-m3 model")
        except ImportError:
            logger.warning("BGE-Reranker not available, ranking disabled")
            self.reranker = None
    
    def rerank(self, query: str, documents: List[str], top_k: int = 10) -> List[Dict]:
        """Rerank documents based on relevance to query"""
        if self.reranker is None or not documents:
            return [
                {"index": i, "score": 1.0 / (i + 1)} 
                for i in range(min(top_k, len(documents)))
            ]
        
        try:
            # Format: [(query, doc), (query, doc), ...]
            pairs = [[query, doc] for doc in documents]
            scores = self.reranker.compute_score(pairs)
            
            ranked = sorted(
                enumerate(scores),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]
            
            return [
                {"index": idx, "score": float(score)}
                for idx, score in ranked
            ]
        except Exception as e:
            logger.error(f"Error reranking documents: {e}")
            return [
                {"index": i, "score": 1.0 / (i + 1)}
                for i in range(min(top_k, len(documents)))
            ]
