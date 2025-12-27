"""
BRD Agent - Embedding Service
Ollama-based embedding generation for RAG.
"""

from typing import List, Optional
import httpx
import logging

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service using Ollama API.
    
    Generates embeddings for text using the configured Ollama embedding model.
    Supports single and batch embedding generation.
    """
    
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize Ollama embedding service.
        
        Args:
            ollama_url: Optional Ollama API URL. If None, uses config value.
            model_name: Optional model name. If None, uses config value.
        """
        settings = get_settings()
        self.ollama_url = (ollama_url or settings.ollama_embedding_url).rstrip('/')
        self.model_name = model_name or settings.ollama_embedding_model
        
        # Setup httpx client with timeout
        self.client = httpx.Client(
            base_url=self.ollama_url,
            timeout=30.0,  # 30 second timeout for embedding generation
        )
        
        logger.info(
            f"EmbeddingService initialized: {self.ollama_url}, model: {self.model_name}"
        )
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector (768 dimensions for nomic-embed-text)
            
        Raises:
            httpx.HTTPError: If Ollama API request fails
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = self.client.post(
                "/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "embedding" not in data:
                raise ValueError(f"Invalid response from Ollama API: {data}")
            
            embedding = data["embedding"]
            
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            
            return embedding
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Currently processes sequentially. Future optimization could use
        parallel requests or Ollama's batch endpoint if available.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors (same order as input texts)
            
        Raises:
            ValueError: If texts list is empty
            httpx.HTTPError: If any embedding request fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.embed(text)
                embeddings.append(embedding)
                logger.debug(f"Processed {i+1}/{len(texts)} texts")
            except Exception as e:
                logger.error(f"Failed to embed text {i+1}: {e}")
                raise
        
        logger.info(f"Generated {len(embeddings)} embeddings for {len(texts)} texts")
        
        return embeddings
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model information:
            - 'model_name': Model name
            - 'ollama_url': Ollama API URL
            - 'dimension': Embedding dimension (768 for nomic-embed-text)
            
        Note: Dimension is hardcoded for nomic-embed-text. Future versions
        could query Ollama API to get actual model info.
        """
        # For nomic-embed-text, dimension is 768
        # Future: Could query Ollama API to get actual model info
        dimension = 768  # nomic-embed-text dimension
        
        return {
            "model_name": self.model_name,
            "ollama_url": self.ollama_url,
            "dimension": dimension,
        }
    
    def __del__(self):
        """Cleanup httpx client on deletion"""
        if hasattr(self, 'client'):
            try:
                self.client.close()
            except Exception:
                pass

