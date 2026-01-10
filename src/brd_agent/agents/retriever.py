"""
BRD Agent - Retriever Agent
Retrieves relevant context from ingested repositories for BRD processing.
Supports both basic retrieval (Step 9) and query expansion (Step 10).
"""

import logging
import hashlib
import re
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
        repo_url: Optional[str] = None,
        use_query_expansion: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from ingested repository.
        
        Args:
            parsed_brd: Parsed BRD object containing business requirements
            repo_url: Optional repository URL. If not provided, uses default from config.
            use_query_expansion: Whether to use query expansion (default: True). 
                                If False, uses basic single-query retrieval.
        
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
        
        if use_query_expansion:
            return self._retrieve_with_query_expansion(parsed_brd, target_repo_url)
        else:
            return self._retrieve_basic(parsed_brd, target_repo_url)
    
    def _retrieve_basic(
        self,
        parsed_brd: ParsedBRD,
        target_repo_url: str
    ) -> List[Dict[str, Any]]:
        """
        Basic retrieval using single query (Step 9 behavior).
        
        Args:
            parsed_brd: Parsed BRD object
            target_repo_url: Repository URL to query
        
        Returns:
            List of relevant document chunks
        """
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
        logger.info(f"{self.name}: Retrieved {len(formatted_results)} relevant chunks (basic)")
        
        return formatted_results
    
    def _retrieve_with_query_expansion(
        self,
        parsed_brd: ParsedBRD,
        target_repo_url: str
    ) -> List[Dict[str, Any]]:
        """
        Advanced retrieval using query expansion (Step 10).
        
        Args:
            parsed_brd: Parsed BRD object
            target_repo_url: Repository URL to query
        
        Returns:
            List of relevant document chunks (merged and deduplicated)
        """
        # Step 1: Generate expanded queries using LLM
        try:
            expanded_queries = self._generate_expanded_queries(parsed_brd)
            logger.info(f"{self.name}: Generated {len(expanded_queries)} expanded queries")
        except Exception as e:
            logger.warning(f"{self.name}: Failed to generate expanded queries: {e}. Falling back to basic retrieval.")
            return self._retrieve_basic(parsed_brd, target_repo_url)
        
        # Step 2: Generate embeddings for each query
        try:
            query_embeddings = self.embedding_service.embed_batch(expanded_queries)
            logger.debug(f"{self.name}: Generated {len(query_embeddings)} query embeddings")
        except Exception as e:
            logger.error(f"{self.name}: Failed to generate embeddings: {e}")
            raise ValueError(f"Failed to generate embeddings for expanded queries: {e}")
        
        # Step 3: Query ChromaDB for each query
        all_results = []
        for i, (query, query_embedding) in enumerate(zip(expanded_queries, query_embeddings)):
            try:
                results = self.vector_store.query(
                    repo_url=target_repo_url,
                    query_embedding=query_embedding,
                    top_k=self.settings.rag_top_k
                )
                formatted = self._format_results(results)
                # Tag results with query info
                for result in formatted:
                    result['query_index'] = i
                    result['query'] = query
                all_results.extend(formatted)
                logger.debug(f"{self.name}: Query {i+1} returned {len(formatted)} results")
            except ValueError as e:
                logger.warning(f"{self.name}: Collection not found for {target_repo_url}: {e}")
                return []
            except Exception as e:
                logger.warning(f"{self.name}: Query {i+1} failed: {e}. Continuing with other queries.")
                continue
        
        # Step 4: Merge and deduplicate results
        merged_results = self._merge_and_deduplicate(all_results)
        logger.debug(f"{self.name}: Merged {len(all_results)} results into {len(merged_results)} unique chunks")
        
        # Step 5: Rank by relevance
        ranked_results = self._rank_by_relevance(merged_results)
        
        # Step 6: Return top-K chunks
        top_k_results = ranked_results[:self.settings.rag_top_k]
        logger.info(f"{self.name}: Retrieved {len(top_k_results)} relevant chunks (query expansion)")
        
        return top_k_results
    
    def _generate_expanded_queries(self, parsed_brd: ParsedBRD) -> List[str]:
        """
        Generate targeted queries from BRD using LLM with comprehensive BRD analysis.
        
        Uses the COMPLETE BRD structure (not just summary) to generate queries that cover:
        - Each business objective (1-2 queries per objective)
        - Each functional requirement (1 query per requirement)
        - Architecture/pattern queries (2-3 queries)
        
        Query count is dynamic based on BRD complexity, limited by rag_query_count.
        
        Args:
            parsed_brd: Parsed BRD object
        
        Returns:
            List of query strings with traceability to BRD components
        """
        # Build comprehensive BRD context for query generation
        brd_context = self._build_comprehensive_brd_context(parsed_brd)
        
        # Calculate dynamic query count based on BRD complexity
        num_objectives = len(parsed_brd.business_objectives) if parsed_brd.business_objectives else 0
        num_requirements = len(parsed_brd.requirements.functional) if parsed_brd.requirements and parsed_brd.requirements.functional else 0
        architecture_queries = 3
        
        # Dynamic query count: min(config_limit, calculated_count)
        calculated_count = (num_objectives * 2) + num_requirements + architecture_queries
        target_query_count = min(self.settings.rag_query_count, calculated_count)
        
        # Ensure at least 3 queries
        target_query_count = max(3, target_query_count)
        
        logger.info(
            f"{self.name}: Generating queries - BRD has {num_objectives} objectives, "
            f"{num_requirements} requirements. Target: {target_query_count} queries"
        )
        
        prompt = f"""Analyze the following COMPLETE business requirements document and generate {target_query_count} specific, targeted search queries that would help find relevant documentation in a codebase.

CRITICAL REQUIREMENTS:
1. Generate queries that cover EACH business objective (1-2 queries per objective)
2. Generate queries that cover EACH functional requirement (1 query per requirement)
3. Generate 2-3 additional queries for architecture/patterns/integration points

Each query should be:
- Specific and actionable (5-15 words)
- Focused on technical patterns, features, architecture, or integration points
- Traceable to specific BRD components (objectives or requirements)

BRD Structure:
{brd_context}

Generate exactly {target_query_count} queries, one per line. Format: one query per line, no numbering needed.

Queries:"""

        try:
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.7
            )
            
            # Parse queries from response
            # Handle various formats: numbered lists, bullet points, plain lines
            lines = response.strip().split('\n')
            queries = []
            
            # Skip preamble lines (common LLM patterns)
            skip_patterns = [
                r'^here are',
                r'^based on',
                r'^the following',
                r'^these queries',
                r'^queries:',
                r'^query:',
                r'^the queries',
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip comment lines
                if line.startswith('#'):
                    continue
                
                # Skip preamble lines
                line_lower = line.lower()
                if any(re.match(pattern, line_lower) for pattern in skip_patterns):
                    continue
                
                # Remove numbering (e.g., "1. ", "1) ", "- ")
                line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove "1. " or "1) "
                line = re.sub(r'^[-•]\s*', '', line)  # Remove "- " or "• "
                # Remove quotes (both wrapping and internal)
                line = re.sub(r'["\']', '', line)  # Remove all quotes
                line = line.strip()
                
                # Extract query from lines that might have explanatory text
                # Look for patterns like "Search for X" or "Investigate Y" or just the query itself
                # If line is too long (>100 chars), try to extract the core query
                if len(line) > 100:
                    # Try to extract query from patterns like "Search for X to find Y"
                    match = re.search(r'(?:search for|investigate|locate|explore|analyze|identify)\s+([^.]{5,80})', line_lower)
                    if match:
                        line = match.group(1).strip()
                    else:
                        # Take first part before common separators
                        parts = re.split(r'[.,;]', line)
                        if parts:
                            line = parts[0].strip()
                
                # Clean up common prefixes
                line = re.sub(r'^(search for|investigate|locate|explore|analyze|identify|find)\s+', '', line_lower)
                line = line.strip()
                
                # Validate query (5-80 chars, not just numbers/punctuation)
                if line and 5 <= len(line) <= 80 and re.search(r'[a-zA-Z]', line):
                    queries.append(line)
            
            # Limit to target query count
            queries = queries[:target_query_count]
            
            # Ensure we have at least one query
            if not queries:
                logger.warning(f"{self.name}: LLM generated no queries, using fallback")
                brd_summary = self._extract_brd_summary(parsed_brd)
                queries = [brd_summary[:200]]  # Fallback to summary
            
            logger.info(
                f"{self.name}: Generated {len(queries)} queries covering "
                f"{num_objectives} objectives and {num_requirements} requirements"
            )
            logger.debug(f"{self.name}: Generated queries: {queries}")
            
            return queries
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to generate expanded queries: {e}")
            raise
    
    def _merge_and_deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate results from multiple queries.
        
        Deduplicates by content hash. If same content appears multiple times,
        keeps the one with the lowest distance (most relevant).
        
        Args:
            results: List of result chunks from multiple queries
        
        Returns:
            Deduplicated list of chunks
        """
        seen = {}  # content_hash -> best_result
        
        for result in results:
            # Create hash of content for deduplication
            content_hash = hashlib.md5(result['content'].encode()).hexdigest()
            
            if content_hash not in seen:
                seen[content_hash] = result
            else:
                # Keep the one with lower distance (more relevant)
                existing = seen[content_hash]
                if result['distance'] is not None and existing['distance'] is not None:
                    if result['distance'] < existing['distance']:
                        seen[content_hash] = result
                elif result['distance'] is not None:
                    # Current has distance, existing doesn't - prefer current
                    seen[content_hash] = result
        
        return list(seen.values())
    
    def _rank_by_relevance(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank results by relevance (distance score).
        
        Lower distance = more relevant, so sort ascending.
        Results without distance go to the end.
        
        Args:
            results: List of result chunks
        
        Returns:
            Ranked list (most relevant first)
        """
        # Separate results with and without distance
        with_distance = [r for r in results if r.get('distance') is not None]
        without_distance = [r for r in results if r.get('distance') is None]
        
        # Sort by distance (ascending - lower is better)
        with_distance.sort(key=lambda x: x['distance'])
        
        # Combine: with distance first, then without
        return with_distance + without_distance
    
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
    
    def _build_comprehensive_brd_context(self, parsed_brd: ParsedBRD) -> str:
        """
        Build comprehensive BRD context for query generation.
        
        Includes ALL BRD components:
        - Executive summary
        - All business objectives (with priorities and success criteria)
        - All functional requirements (with descriptions and priorities)
        - Optional: non-functional requirements, project scope
        
        Args:
            parsed_brd: Parsed BRD object
        
        Returns:
            Formatted BRD context string
        """
        parts = []
        
        # Executive Summary
        if parsed_brd.executive_summary:
            parts.append("EXECUTIVE SUMMARY:")
            parts.append(parsed_brd.executive_summary)
            parts.append("")
        
        # Business Objectives
        if parsed_brd.business_objectives:
            parts.append("BUSINESS OBJECTIVES:")
            for i, obj in enumerate(parsed_brd.business_objectives, 1):
                obj_text = f"  {obj.id}: {obj.objective}"
                if obj.priority:
                    obj_text += f" (Priority: {obj.priority})"
                if obj.metric_success_criteria:
                    obj_text += f"\n    Success Criteria: {obj.metric_success_criteria}"
                parts.append(obj_text)
            parts.append("")
        
        # Functional Requirements
        if parsed_brd.requirements and parsed_brd.requirements.functional:
            parts.append("FUNCTIONAL REQUIREMENTS:")
            for req in parsed_brd.requirements.functional:
                req_text = f"  {req.id}: {req.description}"
                if req.priority:
                    req_text += f" (Priority: {req.priority})"
                parts.append(req_text)
            parts.append("")
        
        # Non-functional Requirements (optional)
        if parsed_brd.requirements and parsed_brd.requirements.non_functional:
            parts.append("NON-FUNCTIONAL REQUIREMENTS:")
            for nfr in parsed_brd.requirements.non_functional:
                nfr_text = f"  {nfr.id}: {nfr.description}"
                if nfr.priority:
                    nfr_text += f" (Priority: {nfr.priority})"
                parts.append(nfr_text)
            parts.append("")
        
        # Project Scope (optional)
        if parsed_brd.project_scope:
            if parsed_brd.project_scope.in_scope:
                parts.append("IN SCOPE:")
                for item in parsed_brd.project_scope.in_scope:
                    parts.append(f"  - {item}")
                parts.append("")
        
        return "\n".join(parts)
    
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

