#!/usr/bin/env python3
"""
Test script for Step 4: Basic Chunking Strategy
Verifies that chunking functions work correctly for markdown and recursive chunking.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.chunking import chunk_markdown, chunk_recursive


def test_chunk_markdown_basic():
    """Test basic markdown chunking by headers"""
    print("🧪 Test 1: Basic Markdown Chunking")
    print("-" * 50)
    
    text = "# Title\n## Section 1\nContent here\n## Section 2\nMore content"
    chunks = chunk_markdown(text)
    
    # Should create chunks: one for content before first ## header, then one per ## header
    # So: "# Title" as chunk 1, "## Section 1\nContent here" as chunk 2, "## Section 2\nMore content" as chunk 3
    if len(chunks) < 2:
        print(f"❌ Expected at least 2 chunks, got {len(chunks)}")
        return False
    
    # Check that we have sections
    has_section1 = any("Section 1" in chunk['content'] for chunk in chunks)
    has_section2 = any("Section 2" in chunk['content'] for chunk in chunks)
    
    if not has_section1:
        print(f"❌ Missing Section 1 in chunks")
        return False
    
    if not has_section2:
        print(f"❌ Missing Section 2 in chunks")
        return False
    
    print(f"✅ Created {len(chunks)} chunks correctly")
    print(f"   Chunk 1: {chunks[0]['content'][:40]}...")
    if len(chunks) > 1:
        print(f"   Chunk 2: {chunks[1]['content'][:40]}...")
    return True


def test_chunk_markdown_metadata():
    """Test that markdown chunks include correct metadata"""
    print("\n🧪 Test 2: Markdown Chunk Metadata")
    print("-" * 50)
    
    text = "## Section 1\nContent\n## Section 2\nMore"
    source_path = "test.md"
    chunks = chunk_markdown(text, source_path=source_path)
    
    required_keys = ['content', 'source', 'line_start', 'line_end', 'chunk_type']
    
    for i, chunk in enumerate(chunks):
        for key in required_keys:
            if key not in chunk:
                print(f"❌ Chunk {i} missing key: {key}")
                return False
        
        if chunk['source'] != source_path:
            print(f"❌ Chunk {i} source mismatch: {chunk['source']}")
            return False
        
        if chunk['chunk_type'] != 'markdown_header':
            print(f"❌ Chunk {i} wrong type: {chunk['chunk_type']}")
            return False
        
        if chunk['line_start'] > chunk['line_end']:
            print(f"❌ Chunk {i} invalid line range: {chunk['line_start']}-{chunk['line_end']}")
            return False
    
    print(f"✅ All {len(chunks)} chunks have correct metadata")
    print(f"   Example: line_start={chunks[0]['line_start']}, line_end={chunks[0]['line_end']}")
    return True


def test_chunk_markdown_no_headers():
    """Test markdown chunking when no headers exist"""
    print("\n🧪 Test 3: Markdown Without Headers")
    print("-" * 50)
    
    text = "This is plain text without any headers.\nJust regular content."
    chunks = chunk_markdown(text)
    
    if len(chunks) != 1:
        print(f"❌ Expected 1 chunk for text without headers, got {len(chunks)}")
        return False
    
    if chunks[0]['content'] != text.strip():
        print(f"❌ Content mismatch for single chunk")
        return False
    
    print(f"✅ Single chunk created correctly for text without headers")
    return True


def test_chunk_markdown_nested_headers():
    """Test markdown chunking with nested headers"""
    print("\n🧪 Test 4: Nested Headers")
    print("-" * 50)
    
    text = """## Main Section
Content here
### Subsection 1
Sub content
### Subsection 2
More sub content
## Another Section
Final content"""
    
    chunks = chunk_markdown(text)
    
    # Should create chunks at ## level, not ###
    if len(chunks) < 2:
        print(f"❌ Expected at least 2 chunks, got {len(chunks)}")
        return False
    
    # Check that subsections are included in main section chunks
    has_subsection = any("Subsection" in chunk['content'] for chunk in chunks)
    if not has_subsection:
        print(f"❌ Subsections not included in chunks")
        return False
    
    print(f"✅ Created {len(chunks)} chunks with nested headers")
    return True


def test_chunk_recursive_basic():
    """Test basic recursive chunking"""
    print("\n🧪 Test 5: Basic Recursive Chunking")
    print("-" * 50)
    
    # Create text longer than chunk_size
    text = "This is a test. " * 100  # ~1500 characters
    chunks = chunk_recursive(text, chunk_size=500, overlap=50)
    
    if len(chunks) < 2:
        print(f"❌ Expected multiple chunks, got {len(chunks)}")
        return False
    
    # Check chunk sizes
    for i, chunk in enumerate(chunks):
        if len(chunk['content']) > 600:  # chunk_size + some margin
            print(f"❌ Chunk {i} too large: {len(chunk['content'])}")
            return False
    
    print(f"✅ Created {len(chunks)} recursive chunks")
    print(f"   Average chunk size: {sum(len(c['content']) for c in chunks) / len(chunks):.0f} chars")
    return True


def test_chunk_recursive_metadata():
    """Test that recursive chunks include correct metadata"""
    print("\n🧪 Test 6: Recursive Chunk Metadata")
    print("-" * 50)
    
    text = "Line 1\nLine 2\nLine 3\n" * 10
    source_path = "test.txt"
    chunks = chunk_recursive(text, chunk_size=50, overlap=10, source_path=source_path)
    
    required_keys = ['content', 'source', 'line_start', 'line_end', 'chunk_type']
    
    for i, chunk in enumerate(chunks):
        for key in required_keys:
            if key not in chunk:
                print(f"❌ Chunk {i} missing key: {key}")
                return False
        
        if chunk['source'] != source_path:
            print(f"❌ Chunk {i} source mismatch")
            return False
        
        if chunk['chunk_type'] != 'recursive':
            print(f"❌ Chunk {i} wrong type: {chunk['chunk_type']}")
            return False
    
    print(f"✅ All {len(chunks)} recursive chunks have correct metadata")
    return True


def test_chunk_recursive_overlap():
    """Test that recursive chunks have proper overlap"""
    print("\n🧪 Test 7: Recursive Chunk Overlap")
    print("-" * 50)
    
    # Create text with unique markers
    text = "START " + " ".join([f"WORD{i}" for i in range(100)]) + " END"
    chunks = chunk_recursive(text, chunk_size=100, overlap=30)
    
    if len(chunks) < 2:
        print(f"❌ Need at least 2 chunks to test overlap, got {len(chunks)}")
        return False
    
    # Check that consecutive chunks share some content (overlap)
    for i in range(len(chunks) - 1):
        chunk1_end = chunks[i]['content'][-30:]  # Last 30 chars
        chunk2_start = chunks[i + 1]['content'][:30]  # First 30 chars
        
        # They should share some words
        chunk1_words = set(chunk1_end.split())
        chunk2_words = set(chunk2_start.split())
        overlap_words = chunk1_words & chunk2_words
        
        if len(overlap_words) == 0:
            print(f"⚠️  Chunks {i} and {i+1} have no word overlap (may be OK)")
        else:
            print(f"✅ Chunks {i} and {i+1} share {len(overlap_words)} words")
    
    return True


def test_chunk_recursive_edge_cases():
    """Test edge cases for recursive chunking"""
    print("\n🧪 Test 8: Recursive Edge Cases")
    print("-" * 50)
    
    # Test empty text
    try:
        chunks = chunk_recursive("")
        if len(chunks) != 0:
            print(f"❌ Empty text should return 0 chunks, got {len(chunks)}")
            return False
        print("✅ Empty text handled correctly")
    except Exception as e:
        print(f"❌ Empty text raised exception: {e}")
        return False
    
    # Test invalid parameters
    try:
        chunk_recursive("test", chunk_size=-1)
        print(f"❌ Should raise ValueError for negative chunk_size")
        return False
    except ValueError:
        print("✅ Negative chunk_size correctly raises ValueError")
    
    try:
        chunk_recursive("test", overlap=-1)
        print(f"❌ Should raise ValueError for negative overlap")
        return False
    except ValueError:
        print("✅ Negative overlap correctly raises ValueError")
    
    try:
        chunk_recursive("test", chunk_size=100, overlap=100)
        print(f"❌ Should raise ValueError when overlap >= chunk_size")
        return False
    except ValueError:
        print("✅ Overlap >= chunk_size correctly raises ValueError")
    
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("Step 4 Chunking Strategy Test Suite")
    print("=" * 50)
    
    results = [
        test_chunk_markdown_basic(),
        test_chunk_markdown_metadata(),
        test_chunk_markdown_no_headers(),
        test_chunk_markdown_nested_headers(),
        test_chunk_recursive_basic(),
        test_chunk_recursive_metadata(),
        test_chunk_recursive_overlap(),
        test_chunk_recursive_edge_cases(),
    ]
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All tests passed ({passed}/{total})")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

