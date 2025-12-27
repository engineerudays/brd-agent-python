"""
BRD Agent - Vector Store Service
ChromaDB wrapper for managing vector embeddings of repository documentation.
Supports multiple repositories, each with its own collection.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaDBSettings

from ..config import get_settings


class VectorStore:
    """
    ChromaDB vector store wrapper for repository documentation.
    
    Each repository gets its own ChromaDB collection, allowing multiple
    repositories to coexist in the same vector store.
    """
    
    def __init__(self, chromadb_path: Optional[str] = None):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            chromadb_path: Optional path to ChromaDB persistence directory.
                          If None, uses value from config.
        """
        settings = get_settings()
        self.chromadb_path = Path(chromadb_path or settings.chromadb_path)
        
        # Ensure directory exists
        self.chromadb_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.chromadb_path),
            settings=ChromaDBSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
    
    def get_collection_name(self, repo_url: str) -> str:
        """
        Generate a normalized collection name from repository URL.
        
        Normalizes GitHub URLs to safe identifiers:
        - https://github.com/owner/repo -> owner_repo
        - Handles special characters and normalizes to lowercase
        - Ensures uniqueness for different repos
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            Normalized collection name (safe for ChromaDB)
            
        Example:
            >>> store = VectorStore()
            >>> store.get_collection_name("https://github.com/paperless-ngx/paperless-ngx")
            'paperless-ngx_paperless-ngx'
        """
        # Extract owner/repo from URL
        # Pattern: https://github.com/owner/repo or github.com/owner/repo
        pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/?#]+)'
        match = re.search(pattern, repo_url.lower())
        
        if not match:
            # Fallback: use URL as-is, sanitize
            normalized = re.sub(r'[^a-z0-9_-]', '_', repo_url.lower())
            normalized = re.sub(r'_+', '_', normalized)  # Collapse multiple underscores
            return normalized.strip('_')
        
        owner, repo = match.groups()
        
        # Remove .git suffix if present
        repo = repo.rstrip('.git')
        
        # Normalize: replace special chars with underscore
        owner = re.sub(r'[^a-z0-9_-]', '_', owner)
        repo = re.sub(r'[^a-z0-9_-]', '_', repo)
        
        # Combine and ensure uniqueness
        collection_name = f"{owner}_{repo}"
        
        # Collapse multiple underscores
        collection_name = re.sub(r'_+', '_', collection_name)
        
        return collection_name.strip('_')
    
    def create_collection(self, repo_url: str) -> chromadb.Collection:
        """
        Create a new collection for a repository.
        
        If collection already exists, returns the existing collection.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            ChromaDB Collection object
            
        Raises:
            ValueError: If repo_url is invalid
        """
        collection_name = self.get_collection_name(repo_url)
        
        # Check if collection already exists
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection
        except Exception:
            # Collection doesn't exist, create it
            pass
        
        # Create new collection
        collection = self.client.create_collection(
            name=collection_name,
            metadata={
                "repo_url": repo_url,
                "collection_name": collection_name,
            }
        )
        
        return collection
    
    def get_collection(self, repo_url: str) -> Optional[chromadb.Collection]:
        """
        Get existing collection for a repository.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Returns:
            ChromaDB Collection object if exists, None otherwise
        """
        collection_name = self.get_collection_name(repo_url)
        
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection
        except Exception:
            return None
    
    def add_documents(
        self,
        repo_url: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """
        Add documents to a repository's collection.
        
        Args:
            repo_url: Full GitHub repository URL
            documents: List of document texts (chunks)
            embeddings: List of embedding vectors (same length as documents)
            metadata: List of metadata dicts (same length as documents)
                     Each dict should contain: repo, file_path, doc_type, timestamp, etc.
        
        Raises:
            ValueError: If collection doesn't exist or input lengths don't match
        """
        collection = self.get_collection(repo_url)
        
        if collection is None:
            # Create collection if it doesn't exist
            collection = self.create_collection(repo_url)
        
        # Validate input lengths
        if not (len(documents) == len(embeddings) == len(metadata)):
            raise ValueError(
                f"Documents ({len(documents)}), embeddings ({len(embeddings)}), "
                f"and metadata ({len(metadata)}) must have the same length"
            )
        
        # Generate IDs for documents
        ids = [f"doc_{i}_{hash(doc) % 1000000}" for i, doc in enumerate(documents)]
        
        # Add to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids,
        )
    
    def query(
        self,
        repo_url: str,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents in a repository's collection.
        
        Args:
            repo_url: Full GitHub repository URL
            query_embedding: Query vector embedding
            top_k: Number of results to return (default: 5)
            where: Optional metadata filter (e.g., {"doc_type": "markdown"})
        
        Returns:
            Dictionary with keys:
            - 'ids': List of document IDs
            - 'documents': List of document texts
            - 'metadatas': List of metadata dicts
            - 'distances': List of distance scores
            
        Raises:
            ValueError: If collection doesn't exist
        """
        collection = self.get_collection(repo_url)
        
        if collection is None:
            raise ValueError(
                f"Collection for repository {repo_url} does not exist. "
                "Please ingest the repository first."
            )
        
        # Build query
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        
        if where:
            query_kwargs["where"] = where
        
        # Execute query
        results = collection.query(**query_kwargs)
        
        return results
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all ingested repositories (collections).
        
        Returns:
            List of dictionaries with collection info:
            - 'name': Collection name
            - 'repo_url': Repository URL (from metadata)
            - 'count': Number of documents in collection
        """
        collections = []
        
        for collection in self.client.list_collections():
            try:
                # Get collection metadata
                metadata = collection.metadata or {}
                repo_url = metadata.get("repo_url", "unknown")
                
                # Get document count
                count = collection.count()
                
                collections.append({
                    "name": collection.name,
                    "repo_url": repo_url,
                    "count": count,
                })
            except Exception:
                # Skip collections that can't be accessed
                continue
        
        return collections
    
    def delete_collection(self, repo_url: str) -> None:
        """
        Delete a repository's collection.
        
        Args:
            repo_url: Full GitHub repository URL
            
        Raises:
            ValueError: If collection doesn't exist
        """
        collection = self.get_collection(repo_url)
        
        if collection is None:
            raise ValueError(
                f"Collection for repository {repo_url} does not exist"
            )
        
        self.client.delete_collection(name=collection.name)

