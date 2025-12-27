"""
BRD Agent - Chunking Service
Text chunking strategies for RAG document processing.
"""

import re
from typing import List, Dict, Any, Optional


def chunk_markdown(text: str, source_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Split markdown text by headers (##, ###, ####).
    
    Each section becomes a separate chunk, preserving semantic boundaries.
    Headers are included in the chunk content.
    
    Args:
        text: Markdown text to chunk
        source_path: Optional source file path for metadata
        
    Returns:
        List of chunk dictionaries with:
        - 'content': Chunk text (including header)
        - 'source': Source file path (if provided)
        - 'line_start': Starting line number (1-indexed)
        - 'line_end': Ending line number (1-indexed)
        - 'chunk_type': 'markdown_header'
    """
    if not text or not text.strip():
        return []
    
    lines = text.split('\n')
    chunks = []
    current_chunk_lines = []
    current_start_line = 1
    found_first_header = False
    
    # Pattern to match markdown headers (##, ###, ####)
    header_pattern = re.compile(r'^(#{2,4})\s+(.+)$')
    
    for i, line in enumerate(lines, start=1):
        match = header_pattern.match(line)
        
        if match:
            found_first_header = True
            
            # Save previous chunk if it exists
            if current_chunk_lines:
                chunk_content = '\n'.join(current_chunk_lines).strip()
                if chunk_content:
                    chunks.append({
                        'content': chunk_content,
                        'source': source_path,
                        'line_start': current_start_line,
                        'line_end': i - 1,
                        'chunk_type': 'markdown_header',
                    })
            
            # Start new chunk with header
            current_chunk_lines = [line]
            current_start_line = i
        else:
            # Add line to current chunk
            current_chunk_lines.append(line)
    
    # Add final chunk
    if current_chunk_lines:
        chunk_content = '\n'.join(current_chunk_lines).strip()
        if chunk_content:
            chunks.append({
                'content': chunk_content,
                'source': source_path,
                'line_start': current_start_line,
                'line_end': len(lines),
                'chunk_type': 'markdown_header',
            })
    
    # If no headers found, return entire text as single chunk
    if not found_first_header and not chunks:
        chunks.append({
            'content': text.strip(),
            'source': source_path,
            'line_start': 1,
            'line_end': len(lines),
            'chunk_type': 'markdown_header',
        })
    
    return chunks


def chunk_recursive(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    source_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Split text into fixed-size chunks with overlap (recursive fallback).
    
    Tries to split at paragraph boundaries first, then falls back to
    sentence boundaries, then character boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk (default: 1000)
        overlap: Number of characters to overlap between chunks (default: 200)
        source_path: Optional source file path for metadata
        
    Returns:
        List of chunk dictionaries with:
        - 'content': Chunk text
        - 'source': Source file path (if provided)
        - 'line_start': Starting line number (1-indexed)
        - 'line_end': Ending line number (1-indexed)
        - 'chunk_type': 'recursive'
    """
    if not text or not text.strip():
        return []
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    lines = text.split('\n')
    chunks = []
    
    # Build character-to-line mapping for accurate line tracking
    char_to_line = []
    current_pos = 0
    for line_num, line in enumerate(lines, start=1):
        for _ in range(len(line) + 1):  # +1 for newline
            char_to_line.append(line_num)
        current_pos += len(line) + 1
    
    # Split text into chunks
    text_content = text
    start_pos = 0
    max_iterations = len(text_content) // max(1, chunk_size - overlap) + 10  # Safety limit
    iteration = 0
    
    while start_pos < len(text_content) and iteration < max_iterations:
        iteration += 1
        
        # Calculate end position
        end_pos = min(start_pos + chunk_size, len(text_content))
        
        # Try to find a good break point (paragraph boundary)
        chunk_text = text_content[start_pos:end_pos]
        
        # If not at end of text, try to break at paragraph boundary
        if end_pos < len(text_content):
            # Look for paragraph break (double newline) near the end
            last_paragraph_break = chunk_text.rfind('\n\n')
            if last_paragraph_break > chunk_size * 0.5:  # If break is in second half
                end_pos = start_pos + last_paragraph_break + 2
                chunk_text = text_content[start_pos:end_pos]
            else:
                # Try sentence boundary
                last_sentence_break = max(
                    chunk_text.rfind('. '),
                    chunk_text.rfind('.\n'),
                    chunk_text.rfind('! '),
                    chunk_text.rfind('?\n'),
                )
                if last_sentence_break > chunk_size * 0.7:  # If break is in last 30%
                    end_pos = start_pos + last_sentence_break + 2
                    chunk_text = text_content[start_pos:end_pos]
        
        # Calculate line numbers
        line_start = char_to_line[min(start_pos, len(char_to_line) - 1)] if char_to_line else 1
        line_end = char_to_line[min(end_pos - 1, len(char_to_line) - 1)] if char_to_line else 1
        
        # Create chunk
        chunk_content = chunk_text.strip()
        if chunk_content:
            chunks.append({
                'content': chunk_content,
                'source': source_path,
                'line_start': line_start,
                'line_end': line_end,
                'chunk_type': 'recursive',
            })
        
        # Move start position forward (with overlap)
        if end_pos >= len(text_content):
            break  # Reached end of text
        
        start_pos = max(start_pos + 1, end_pos - overlap)  # Ensure we always advance
    
    return chunks

