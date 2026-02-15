"""
BRD Agent - Ingestion API Endpoints
REST API endpoints for incremental document ingestion into vector store.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.brd_agent.services.github_client import GitHubClient
from src.brd_agent.services.document_loaders import load_markdown
from src.brd_agent.services.chunking import chunk_markdown
from src.brd_agent.services.embeddings import EmbeddingService
from src.brd_agent.services.vector_store import VectorStore
from src.brd_agent.config import get_settings

logger = logging.getLogger(__name__)

# Create router for ingestion endpoints
router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


# === Request/Response Models ===

class IngestDocumentRequest(BaseModel):
    """Request model for single document ingestion"""
    repo_url: str = Field(..., description="GitHub repository URL")
    file_path: str = Field(..., description="Path to document file within repository")
    content: Optional[str] = Field(None, description="Optional: Direct content (if not fetching from GitHub)")


class IngestRepoPathRequest(BaseModel):
    """Request model for repository path ingestion"""
    repo_url: str = Field(..., description="GitHub repository URL")
    path: str = Field(..., description="Path within repository to ingest (e.g., 'docs/')")


class IngestResponse(BaseModel):
    """Response model for ingestion operations"""
    success: bool
    message: str
    repo_url: str
    collection_name: Optional[str] = None
    files_processed: Optional[int] = None
    chunks_created: Optional[int] = None
    errors: Optional[List[str]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IngestionStatusResponse(BaseModel):
    """Response model for ingestion status"""
    repo_url: str
    collection_name: str
    document_count: int
    last_updated: Optional[str] = None
    exists: bool


class RepoListResponse(BaseModel):
    """Response model for repository list"""
    repos: List[Dict[str, Any]]
    total: int


# === Helper Functions ===

def find_markdown_files(repo_tree: List[Dict[str, Any]], path: str = "") -> List[str]:
    """Find all markdown files in repository tree."""
    markdown_files = []
    markdown_extensions = {'.md', '.rst', '.markdown'}
    
    path_prefix = path.rstrip('/') + '/' if path else ''
    
    for item in repo_tree:
        item_path = item.get('path', '')
        item_type = item.get('type', '')
        
        if path_prefix and not item_path.startswith(path_prefix):
            continue
        
        if item_type == 'file' or item_type == 'blob':
            if any(item_path.lower().endswith(ext) for ext in markdown_extensions):
                markdown_files.append(item_path)
    
    return sorted(markdown_files)


def process_file(
    github_client: GitHubClient,
    repo_url: str,
    file_path: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a single markdown file through the ingestion pipeline.
    
    Returns:
        Dictionary with processing results
    """
    try:
        # Fetch file content if not provided
        if content is None:
            content = github_client.get_file_content(repo_url, file_path)
        
        # Load markdown document
        doc = load_markdown(content, file_path)
        
        # Chunk document
        chunks = chunk_markdown(doc.content, doc.source_path)
        
        if not chunks:
            return {
                "success": True,
                "file_path": file_path,
                "chunks_count": 0,
                "error": None,
            }
        
        # Generate embeddings
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)
        
        # Prepare metadata
        timestamp = datetime.utcnow().isoformat()
        metadatas: List[Dict[str, Any]] = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                "repo": repo_url,
                "file_path": chunk['source'],
                "doc_type": "markdown",
                "chunk_type": chunk['chunk_type'],
                "line_start": chunk['line_start'],
                "line_end": chunk['line_end'],
                "chunk_index": i,
                "timestamp": timestamp,
            }
            metadatas.append(metadata)
        
        # Store in vector store
        vector_store.add_documents(
            repo_url=repo_url,
            documents=chunk_texts,
            embeddings=embeddings,
            metadata=metadatas,
        )
        
        return {
            "success": True,
            "file_path": file_path,
            "chunks_count": len(chunks),
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "file_path": file_path,
            "chunks_count": 0,
            "error": str(e),
        }


# === API Endpoints ===

@router.post("/document", response_model=IngestResponse)
async def ingest_document(request: IngestDocumentRequest):
    """
    Ingest a single document from a GitHub repository.
    
    Args:
        request: IngestDocumentRequest with repo_url, file_path, and optional content
    
    Returns:
        IngestResponse with processing results
    """
    logger.info(f"Ingesting document: {request.file_path} from {request.repo_url}")
    
    try:
        # Initialize services
        github_client = GitHubClient()
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        
        # Process file
        result = process_file(
            github_client=github_client,
            repo_url=request.repo_url,
            file_path=request.file_path,
            embedding_service=embedding_service,
            vector_store=vector_store,
            content=request.content,
        )
        
        if result["success"]:
            collection_name = vector_store.get_collection_name(request.repo_url)
            return IngestResponse(
                success=True,
                message=f"Successfully ingested {request.file_path}",
                repo_url=request.repo_url,
                collection_name=collection_name,
                files_processed=1,
                chunks_created=result["chunks_count"],
            )
        else:
            return IngestResponse(
                success=False,
                message=f"Failed to ingest {request.file_path}",
                repo_url=request.repo_url,
                errors=[result["error"]],
            )
            
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(e)}"
        )


@router.post("/repo-path", response_model=IngestResponse)
async def ingest_repo_path(request: IngestRepoPathRequest):
    """
    Ingest all markdown files from a specific path in a GitHub repository.
    
    Args:
        request: IngestRepoPathRequest with repo_url and path
    
    Returns:
        IngestResponse with processing results
    """
    logger.info(f"Ingesting path: {request.path} from {request.repo_url}")
    
    try:
        # Initialize services
        github_client = GitHubClient()
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        
        # Fetch repository tree
        repo_tree = github_client.get_repo_tree(request.repo_url, request.path)
        
        # Find markdown files
        markdown_files = find_markdown_files(repo_tree, request.path)
        
        if not markdown_files:
            return IngestResponse(
                success=False,
                message=f"No markdown files found in path: {request.path}",
                repo_url=request.repo_url,
                files_processed=0,
                chunks_created=0,
            )
        
        # Process files
        results: List[Dict[str, Any]] = []
        total_chunks = 0
        errors: List[str] = []
        
        for file_path in markdown_files:
            result = process_file(
                github_client=github_client,
                repo_url=request.repo_url,
                file_path=file_path,
                embedding_service=embedding_service,
                vector_store=vector_store,
            )
            
            results.append(result)
            if result["success"]:
                total_chunks += result["chunks_count"]
            else:
                errors.append(f"{file_path}: {result['error']}")
        
        successful_files = sum(1 for r in results if r["success"])
        collection_name = vector_store.get_collection_name(request.repo_url)
        
        return IngestResponse(
            success=successful_files > 0,
            message=f"Processed {successful_files}/{len(markdown_files)} files from {request.path}",
            repo_url=request.repo_url,
            collection_name=collection_name,
            files_processed=successful_files,
            chunks_created=total_chunks,
            errors=errors if errors else None,
        )
        
    except Exception as e:
        logger.error(f"Repository path ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Repository path ingestion failed: {str(e)}"
        )


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    repo_url: str = Query(..., description="GitHub repository URL")
):
    """
    Get ingestion status for a specific repository.
    
    Args:
        repo_url: GitHub repository URL
    
    Returns:
        IngestionStatusResponse with collection status
    """
    logger.info(f"Checking ingestion status for: {repo_url}")
    
    try:
        vector_store = VectorStore()
        collection = vector_store.get_collection(repo_url)
        
        if collection is None:
            return IngestionStatusResponse(
                repo_url=repo_url,
                collection_name=vector_store.get_collection_name(repo_url),
                document_count=0,
                exists=False,
            )
        
        doc_count = collection.count()
        
        # Try to get last updated timestamp from metadata
        last_updated = None
        try:
            results = collection.get(limit=1)
            if results.get('metadatas') and len(results['metadatas']) > 0:
                last_updated = results['metadatas'][0].get('timestamp')
        except Exception:
            pass
        
        return IngestionStatusResponse(
            repo_url=repo_url,
            collection_name=vector_store.get_collection_name(repo_url),
            document_count=doc_count,
            last_updated=last_updated,
            exists=True,
        )
        
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ingestion status: {str(e)}"
        )


@router.get("/repos", response_model=RepoListResponse)
async def list_repos():
    """
    List all ingested repositories.
    
    Returns:
        RepoListResponse with list of repositories and their status
    """
    logger.info("Listing all ingested repositories")
    
    try:
        vector_store = VectorStore()
        client = vector_store.client
        
        # Get all collections
        collections = client.list_collections()
        
        repos: List[Dict[str, Any]] = []
        
        for collection in collections:
            try:
                # Extract repo URL from collection name
                # Collection names are in format: repo_<hash>
                # We need to check metadata to get actual repo URL
                results = collection.get(limit=1)
                
                repo_url = None
                if results.get('metadatas') and len(results['metadatas']) > 0:
                    repo_url = results['metadatas'][0].get('repo')
                
                if repo_url:
                    doc_count = collection.count()
                    repos.append({
                        "repo_url": repo_url,
                        "collection_name": collection.name,
                        "document_count": doc_count,
                    })
            except Exception as e:
                logger.warning(f"Failed to process collection {collection.name}: {e}")
                continue
        
        return RepoListResponse(
            repos=repos,
            total=len(repos),
        )
        
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list repositories: {str(e)}"
        )


@router.delete("/document")
async def delete_document(
    repo_url: str = Query(..., description="GitHub repository URL"),
    file_path: str = Query(..., description="Path to document file to remove"),
):
    """
    Remove a specific document from the vector store.
    
    Args:
        repo_url: GitHub repository URL
        file_path: Path to document file to remove
    
    Returns:
        Success message
    """
    logger.info(f"Deleting document: {file_path} from {repo_url}")
    
    try:
        vector_store = VectorStore()
        collection = vector_store.get_collection(repo_url)
        
        if collection is None:
            raise HTTPException(
                status_code=404,
                detail=f"Repository collection not found: {repo_url}"
            )
        
        # Query for documents with matching file_path
        # Note: ChromaDB doesn't have direct delete by metadata, so we need to:
        # 1. Get all documents with matching file_path
        # 2. Delete them by ID
        
        # Get all documents
        results = collection.get()
        
        # Find IDs of documents matching file_path
        ids_to_delete = []
        if results.get('metadatas'):
            for i, metadata in enumerate(results['metadatas']):
                if metadata.get('file_path') == file_path:
                    if results.get('ids'):
                        ids_to_delete.append(results['ids'][i])
        
        if not ids_to_delete:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {file_path}"
            )
        
        # Delete documents
        collection.delete(ids=ids_to_delete)
        
        return {
            "success": True,
            "message": f"Deleted {len(ids_to_delete)} chunk(s) from {file_path}",
            "repo_url": repo_url,
            "file_path": file_path,
            "chunks_deleted": len(ids_to_delete),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.delete("/repo")
async def delete_repo(
    repo_url: str = Query(..., description="GitHub repository URL"),
):
    """
    Remove an entire repository collection from the vector store.
    
    Args:
        repo_url: GitHub repository URL
    
    Returns:
        Success message
    """
    logger.info(f"Deleting repository collection: {repo_url}")
    
    try:
        vector_store = VectorStore()
        collection = vector_store.get_collection(repo_url)
        
        if collection is None:
            raise HTTPException(
                status_code=404,
                detail=f"Repository collection not found: {repo_url}"
            )
        
        collection_name = collection.name
        
        # Delete the collection
        vector_store.client.delete_collection(collection_name)
        
        return {
            "success": True,
            "message": f"Deleted repository collection: {collection_name}",
            "repo_url": repo_url,
            "collection_name": collection_name,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete repository: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete repository: {str(e)}"
        )

