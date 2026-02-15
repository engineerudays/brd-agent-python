"""
BRD Agent - Document Loaders
Loaders for parsing different document types from GitHub repositories.
"""

from .markdown_loader import load_markdown, Document

__all__ = [
    "load_markdown",
    "Document",
]

