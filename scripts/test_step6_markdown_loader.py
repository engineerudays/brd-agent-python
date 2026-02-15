#!/usr/bin/env python3
"""
Test script for Step 6: Markdown Document Loader

Tests the markdown loader by:
1. Fetching README.md from paperless-ngx via GitHubClient
2. Loading it via MarkdownLoader
3. Verifying document structure and metadata
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.github_client import GitHubClient
from src.brd_agent.services.document_loaders import load_markdown, Document
from src.brd_agent.config import get_settings


def test_markdown_loader():
    """Test markdown loader with paperless-ngx README."""
    print("=" * 60)
    print("Step 6: Markdown Document Loader - Test")
    print("=" * 60)
    
    settings = get_settings()
    repo_url = settings.default_repo_url
    
    print(f"\n1. Fetching README.md from {repo_url}...")
    
    try:
        # Initialize GitHub client
        github_client = GitHubClient()
        
        # Fetch README.md content
        readme_content = github_client.get_file_content(repo_url, "README.md")
        print(f"   ✓ Successfully fetched README.md ({len(readme_content)} characters)")
        
    except Exception as e:
        print(f"   ✗ Failed to fetch README.md: {e}")
        return False
    
    print("\n2. Loading markdown document...")
    
    try:
        # Load markdown document
        doc = load_markdown(readme_content, "README.md")
        print(f"   ✓ Successfully loaded markdown document")
        
    except Exception as e:
        print(f"   ✗ Failed to load markdown: {e}")
        return False
    
    print("\n3. Verifying document structure...")
    
    # Verify document structure
    assert isinstance(doc, Document), "Document should be an instance of Document"
    assert doc.doc_type == "markdown", f"Expected doc_type='markdown', got '{doc.doc_type}'"
    assert doc.source_path == "README.md", f"Expected source_path='README.md', got '{doc.source_path}'"
    assert len(doc.content) > 0, "Document content should not be empty"
    assert "metadata" in dir(doc), "Document should have metadata attribute"
    
    print("   ✓ Document structure is valid")
    
    print("\n4. Verifying document metadata...")
    
    # Verify metadata fields
    metadata = doc.metadata
    assert "line_count" in metadata, "Metadata should contain 'line_count'"
    assert "char_count" in metadata, "Metadata should contain 'char_count'"
    assert "word_count" in metadata, "Metadata should contain 'word_count'"
    assert "header_count" in metadata, "Metadata should contain 'header_count'"
    
    print(f"   ✓ Metadata fields present:")
    print(f"     - line_count: {metadata['line_count']}")
    print(f"     - char_count: {metadata['char_count']}")
    print(f"     - word_count: {metadata['word_count']}")
    print(f"     - header_count: {metadata['header_count']}")
    
    if "title" in metadata:
        print(f"     - title: {metadata['title']}")
    
    print("\n5. Verifying content integrity...")
    
    # Verify content matches original
    assert doc.content == readme_content.strip(), "Document content should match original (stripped)"
    assert len(doc.content.split('\n')) == metadata['line_count'], \
        "Line count should match actual lines in content"
    
    print("   ✓ Content integrity verified")
    
    print("\n6. Testing edge cases...")
    
    # Test empty content (should raise error)
    try:
        load_markdown("")
        print("   ✗ Empty content should raise ValueError")
        return False
    except ValueError:
        print("   ✓ Empty content correctly raises ValueError")
    
    # Test None source_path (should use "unknown")
    doc_no_path = load_markdown("# Test\n\nContent", None)
    assert doc_no_path.source_path == "unknown", \
        "None source_path should default to 'unknown'"
    print("   ✓ None source_path handled correctly")
    
    # Test with minimal content
    minimal_doc = load_markdown("# Title\n\nBody text.", "test.md")
    assert minimal_doc.metadata["line_count"] == 3
    assert minimal_doc.metadata["header_count"] == 1
    assert minimal_doc.metadata["title"] == "Title"
    print("   ✓ Minimal content handled correctly")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_markdown_loader()
    sys.exit(0 if success else 1)

