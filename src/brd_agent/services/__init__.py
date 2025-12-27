"""
BRD Agent - Services Module
Shared services like LLM client, PDF parsing, file I/O, vector store, embeddings, chunking, GitHub client
"""

from .llm import LLMService, AnthropicLLM, OllamaLLM, get_llm_service
from .vector_store import VectorStore
from .embeddings import EmbeddingService
from .chunking import chunk_markdown, chunk_recursive
from .github_client import GitHubClient

__all__ = [
    "LLMService",
    "AnthropicLLM",
    "OllamaLLM",
    "get_llm_service",
    "VectorStore",
    "EmbeddingService",
    "chunk_markdown",
    "chunk_recursive",
    "GitHubClient",
]
