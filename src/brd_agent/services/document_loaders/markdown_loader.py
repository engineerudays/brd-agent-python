"""
BRD Agent - Markdown Document Loader
Loads and parses Markdown files from GitHub repositories.
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Document:
    """
    Structured document representation.
    
    Attributes:
        content: Raw document content (markdown text)
        source_path: Path to the source file (e.g., "README.md" or "docs/guide.md")
        doc_type: Type of document (e.g., "markdown")
        metadata: Additional metadata about the document
    """
    content: str
    source_path: str
    doc_type: str = "markdown"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
        
        # Add computed metadata if not present
        if "line_count" not in self.metadata:
            self.metadata["line_count"] = len(self.content.split('\n'))
        
        if "char_count" not in self.metadata:
            self.metadata["char_count"] = len(self.content)
        
        if "word_count" not in self.metadata:
            self.metadata["word_count"] = len(self.content.split())
        
        # Extract title if available (first # header)
        if "title" not in self.metadata:
            title_match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
            if title_match:
                self.metadata["title"] = title_match.group(1).strip()
        
        # Count headers
        if "header_count" not in self.metadata:
            headers = re.findall(r'^#{1,6}\s+', self.content, re.MULTILINE)
            self.metadata["header_count"] = len(headers)


def load_markdown(content: str, source_path: Optional[str] = None) -> Document:
    """
    Load and parse a Markdown document.
    
    This function takes raw markdown content and creates a structured Document
    object with metadata. The content is preserved as-is for downstream processing
    (chunking, embedding).
    
    Args:
        content: Raw markdown text content
        source_path: Optional path to the source file (e.g., "README.md", 
                     "docs/architecture.md"). Used for tracking and metadata.
    
    Returns:
        Document object with:
        - content: Original markdown text
        - source_path: Source file path (or "unknown" if not provided)
        - doc_type: "markdown"
        - metadata: Dictionary containing:
          - line_count: Number of lines in the document
          - char_count: Number of characters
          - word_count: Number of words
          - title: First # header if present
          - header_count: Total number of headers (# through ######)
    
    Example:
        >>> content = "# My Document\\n\\nThis is content."
        >>> doc = load_markdown(content, "README.md")
        >>> doc.source_path
        'README.md'
        >>> doc.metadata["title"]
        'My Document'
        >>> doc.metadata["line_count"]
        3
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    if source_path is None:
        source_path = "unknown"
    
    # Create document with metadata
    doc = Document(
        content=content.strip(),
        source_path=source_path,
        doc_type="markdown",
        metadata={}
    )
    
    return doc

