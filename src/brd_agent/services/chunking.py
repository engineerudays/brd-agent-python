"""
BRD Agent - Chunking Service
Text chunking strategies for RAG document processing.
"""

import re
import ast
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


def detect_language(file_path: str) -> Optional[str]:
    """
    Detect programming language from file extension.
    
    Args:
        file_path: Path to source code file
        
    Returns:
        Language name (e.g., 'python', 'javascript') or None if unknown
    """
    if not file_path:
        return None
    
    # Normalize to lowercase
    file_path_lower = file_path.lower()
    
    # Language extension mapping
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
    }
    
    # Check for extension match
    for ext, lang in language_map.items():
        if file_path_lower.endswith(ext):
            return lang
    
    return None


def _extract_docstring(node: ast.AST) -> Optional[str]:
    """
    Extract docstring from an AST node (function, class, module).
    
    Args:
        node: AST node (FunctionDef, ClassDef, or Module)
        
    Returns:
        Docstring text or None
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, (ast.Str, ast.Constant))):
            docstring_node = node.body[0].value
            if isinstance(docstring_node, ast.Str):
                return docstring_node.s
            elif isinstance(docstring_node, ast.Constant) and isinstance(docstring_node.value, str):
                return docstring_node.value
    return None


def _get_node_source(code: str, node: ast.AST) -> str:
    """
    Extract source code for an AST node.
    
    Args:
        code: Full source code
        node: AST node
        
    Returns:
        Source code string for the node
    """
    lines = code.split('\n')
    # AST line numbers are 1-indexed
    start_line = node.lineno - 1
    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
    
    # Extract lines (inclusive)
    node_lines = lines[start_line:end_line]
    return '\n'.join(node_lines)


def chunk_code(
    code: str,
    language: Optional[str] = None,
    source_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Split source code by functions and classes (code-aware chunking).
    
    For Python, uses AST parsing to extract functions and classes.
    Each function/class becomes a separate chunk, preserving hierarchy
    (nested functions are included in parent function chunk).
    
    Args:
        code: Source code text
        language: Programming language (e.g., 'python'). If None, detected from source_path
        source_path: Optional source file path for metadata and language detection
        
    Returns:
        List of chunk dictionaries with:
        - 'content': Function/class code (signature + docstring + body)
        - 'source': Source file path (if provided)
        - 'line_start': Starting line number (1-indexed)
        - 'line_end': Ending line number (1-indexed)
        - 'chunk_type': 'code_function' or 'code_class'
        - 'language': Programming language
        - 'name': Function/class name
        - 'has_docstring': Boolean indicating if docstring exists
        - 'parent': Parent function/class name (if nested)
    """
    if not code or not code.strip():
        return []
    
    # Detect language if not provided
    if language is None and source_path:
        language = detect_language(source_path)
    
    # Currently only Python is supported
    if language != 'python':
        # For non-Python languages, fall back to recursive chunking
        # TODO: Add support for other languages using regex/tree-sitter
        return chunk_recursive(code, chunk_size=1000, overlap=200, source_path=source_path)
    
    try:
        # Parse Python code into AST
        tree = ast.parse(code)
    except SyntaxError as e:
        # If parsing fails, fall back to recursive chunking
        return chunk_recursive(code, chunk_size=1000, overlap=200, source_path=source_path)
    
    chunks = []
    lines = code.split('\n')
    
    def process_node(node: ast.AST, parent_name: Optional[str] = None):
        """
        Recursively process AST nodes to extract functions and classes.
        
        Args:
            node: AST node to process
            parent_name: Name of parent function/class (for nested functions)
        """
        # Process classes
        if isinstance(node, ast.ClassDef):
            class_source = _get_node_source(code, node)
            docstring = _extract_docstring(node)
            
            # Create chunk for class (methods are included in the content)
            chunks.append({
                'content': class_source,  # This already includes all methods in the body
                'source': source_path,
                'line_start': node.lineno,
                'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                'chunk_type': 'code_class',
                'language': 'python',
                'name': node.name,
                'has_docstring': docstring is not None,
                'parent': parent_name,
            })
            
            # Note: Methods are NOT processed separately - they're included in class content
            # This preserves the hierarchy as requested
        
        # Process functions (both sync and async)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_source = _get_node_source(code, node)
            docstring = _extract_docstring(node)
            
            # Create chunk for function (nested functions are included in the content)
            chunks.append({
                'content': func_source,  # This already includes nested functions in the body
                'source': source_path,
                'line_start': node.lineno,
                'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                'chunk_type': 'code_function',
                'language': 'python',
                'name': node.name,
                'has_docstring': docstring is not None,
                'parent': parent_name,
            })
            
            # Note: Nested functions are NOT processed separately - they're included in parent function content
            # This preserves the hierarchy as requested
    
    # Track processed nodes to avoid duplicates
    processed_nodes = set()
    
    def process_node_safe(node: ast.AST, parent_name: Optional[str] = None):
        """Wrapper to avoid processing same node twice."""
        node_id = id(node)
        if node_id in processed_nodes:
            return
        processed_nodes.add(node_id)
        process_node(node, parent_name)
    
    # Process all top-level functions and classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            process_node_safe(node)
    
    return chunks

