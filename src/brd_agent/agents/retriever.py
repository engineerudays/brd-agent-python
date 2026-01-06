"""
BRD Agent - Retriever Agent
Retrieves relevant context from ingested repositories for BRD processing.
"""

import logging
from typing import List, Dict, Any, Optional

from .base import BaseAgent
from ..models.brd import ParsedBRD
from ..services.embeddings import EmbeddingService
from ..services.vector_store import VectorStore
from ..config import get_settings


logger = logging.getLogger(__name__)


class RetrieverAgent(BaseAgent):
    """
    Retriever Agent - Retrieves relevant context from ingested repositories.
    
    Takes a ParsedBRD and retrieves relevant document chunks from the
    specified repository's vector store to provide context for planning.
    """
    
    name = "RetrieverAgent"
    description = "Retrieves relevant context from ingested repositories"
    
    def __init__(
        self,
        llm_service=None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        **kwargs
    ):
        """
        Initialize RetrieverAgent.
        
        Args:
            llm_service: LLM service (for future query expansion, not used in basic version)
            embedding_service: Embedding service for generating query embeddings
            vector_store: Vector store for querying ChromaDB
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(llm_service=llm_service, **kwargs)
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.settings = get_settings()
        
        logger.info(f"{self.name}: Initialized with embedding service and vector store")
    
    def run(
        self,
        parsed_brd: ParsedBRD,
        repo_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from ingested repository.
        
        Args:
            parsed_brd: Parsed BRD object containing business requirements
            repo_url: Optional repository URL. If not provided, uses default from config.
        
        Returns:
            List of relevant document chunks, each containing:
            - 'content': Chunk text content
            - 'source': Source file path
            - 'metadata': Full metadata dict (repo, file_path, line_start, line_end, etc.)
            - 'distance': Similarity distance score (lower = more similar)
        
        Raises:
            ValueError: If repository collection doesn't exist
        """
        logger.info(f"{self.name}: Starting retrieval for BRD: {parsed_brd.document_info.title}")
        
        # Step 1: Determine repository URL
        target_repo_url = repo_url or self.settings.default_repo_url
        logger.debug(f"{self.name}: Using repository: {target_repo_url}")
        
        # Step 2: Extract key terms from BRD
        brd_summary = self._extract_brd_summary(parsed_brd)
        logger.debug(f"{self.name}: Extracted BRD summary ({len(brd_summary)} chars)")
        
        # Step 3: Generate embedding for BRD summary
        try:
            query_embedding = self.embedding_service.embed(brd_summary)
            logger.debug(f"{self.name}: Generated query embedding ({len(query_embedding)} dimensions)")
        except Exception as e:
            logger.error(f"{self.name}: Failed to generate embedding: {e}")
            raise ValueError(f"Failed to generate embedding for BRD summary: {e}")
        
        # Step 4: Query ChromaDB collection for the specified repo
        try:
            results = self.vector_store.query(
                repo_url=target_repo_url,
                query_embedding=query_embedding,
                top_k=self.settings.rag_top_k
            )
            logger.debug(f"{self.name}: Query returned results from ChromaDB")
        except ValueError as e:
            # Collection doesn't exist - return empty list gracefully
            logger.warning(f"{self.name}: Collection not found for {target_repo_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"{self.name}: Failed to query vector store: {e}")
            raise
        
        # Step 5: Format and return top-K chunks with source metadata
        formatted_results = self._format_results(results)
        logger.info(f"{self.name}: Retrieved {len(formatted_results)} relevant chunks")
        
        return formatted_results
    
    def _extract_brd_summary(self, parsed_brd: ParsedBRD) -> str:
        """
        Extract a summary text from ParsedBRD for embedding generation.
        
        Combines executive summary and business objectives to create
        a meaningful query for retrieval.
        
        Args:
            parsed_brd: Parsed BRD object
        
        Returns:
            Summary text string
        """
        parts = []
        
        # Add executive summary if available
        if parsed_brd.executive_summary:
            parts.append(f"Executive Summary: {parsed_brd.executive_summary}")
        
        # Add business objectives
        if parsed_brd.business_objectives:
            objectives_text = ", ".join([
                obj.objective for obj in parsed_brd.business_objectives
            ])
            parts.append(f"Business Objectives: {objectives_text}")
        
        # Add project name/description
        if parsed_brd.document_info.title:
            parts.append(f"Project: {parsed_brd.document_info.title}")
        
        # Add functional requirements summary
        if parsed_brd.requirements and parsed_brd.requirements.functional:
            req_summary = ", ".join([
                req.description[:100] for req in parsed_brd.requirements.functional[:5]
            ])
            if req_summary:
                parts.append(f"Key Requirements: {req_summary}")
        
        # Combine all parts
        summary = "\n\n".join(parts)
        
        # Fallback if nothing extracted
        if not summary.strip():
            summary = "Business requirements document"
        
        return summary
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format ChromaDB query results into a clean list of chunks.
        
        Args:
            results: Raw ChromaDB query results dictionary
        
        Returns:
            List of formatted chunk dictionaries
        """
        formatted = []
        
        # ChromaDB returns nested lists: results['documents'][0] contains the actual list
        if not results or 'documents' not in results:
            return formatted
        
        documents = results.get('documents', [[]])[0] if results.get('documents') else []
        metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
        distances = results.get('distances', [[]])[0] if results.get('distances') else []
        
        for i, doc_content in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            
            formatted.append({
                'content': doc_content,
                'source': metadata.get('file_path', 'unknown'),
                'metadata': metadata,
                'distance': distance,
            })
        
        return formatted

