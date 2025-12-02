"""
BRD Agent - Services Module
Shared services like LLM client, PDF parsing, file I/O
"""

from .llm import LLMService, AnthropicLLM, OllamaLLM, get_llm_service

__all__ = [
    "LLMService",
    "AnthropicLLM",
    "OllamaLLM",
    "get_llm_service",
]
