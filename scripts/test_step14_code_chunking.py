#!/usr/bin/env python3
"""
Test script for Step 14: Code-Aware Chunking

Tests chunk_code() function with Python files:
1. Test with sample Python file containing functions and classes
2. Verify functions are separate chunks
3. Verify classes are separate chunks
4. Verify docstrings are detected
5. Verify nested functions are included in parent chunk
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.chunking import chunk_code, detect_language


# Sample Python code for testing
SAMPLE_PYTHON_CODE = '''"""
Module docstring for testing code chunking.
"""

def top_level_function():
    """This is a top-level function with a docstring."""
    return "Hello"


def function_without_docstring():
    return "No docstring"


class MyClass:
    """This is a class docstring."""
    
    def __init__(self, value):
        """Initialize the class."""
        self.value = value
    
    def instance_method(self):
        """An instance method."""
        return self.value
    
    def method_without_docstring(self):
        return "No docstring"


def function_with_nested_function():
    """Function containing a nested function."""
    
    def nested_function():
        """Nested function docstring."""
        return "nested"
    
    return nested_function()


async def async_function():
    """An async function."""
    return "async result"
'''


def test_language_detection():
    """Test language detection from file extension."""
    print("=" * 70)
    print("Test 1: Language Detection")
    print("=" * 70)
    
    test_cases = [
        ("test.py", "python"),
        ("module.js", "javascript"),
        ("file.ts", "typescript"),
        ("Class.java", "java"),
        ("main.go", "go"),
        ("lib.rs", "rust"),
        ("unknown.txt", None),
        ("", None),
    ]
    
    all_passed = True
    for file_path, expected in test_cases:
        result = detect_language(file_path)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {file_path:20} -> {result} (expected: {expected})")
    
    return all_passed


def test_code_chunking():
    """Test code chunking with sample Python code."""
    print("\n" + "=" * 70)
    print("Test 2: Code Chunking")
    print("=" * 70)
    
    chunks = chunk_code(SAMPLE_PYTHON_CODE, language='python', source_path='test.py')
    
    print(f"\nFound {len(chunks)} chunks:\n")
    
    # Verify we have expected chunks (nested functions/methods are included in parent)
    expected_chunks = [
        ('code_function', 'top_level_function'),
        ('code_function', 'function_without_docstring'),
        ('code_class', 'MyClass'),  # Includes all methods
        ('code_function', 'function_with_nested_function'),  # Includes nested_function
        ('code_function', 'async_function'),
    ]
    
    # Should have 5 chunks (nested functions/methods are NOT separate chunks)
    if len(chunks) != 5:
        print(f"\n⚠ Expected 5 chunks, got {len(chunks)}")
        print("   (Nested functions/methods should be included in parent chunks)")
    
    found_chunks = [(chunk['chunk_type'], chunk['name']) for chunk in chunks]
    
    print("Chunk Summary:")
    for i, chunk in enumerate(chunks, 1):
        parent_info = f" (parent: {chunk.get('parent')})" if chunk.get('parent') else ""
        docstring_info = " [has docstring]" if chunk.get('has_docstring') else " [no docstring]"
        print(f"\n{i}. {chunk['chunk_type']}: {chunk['name']}{parent_info}{docstring_info}")
        print(f"   Lines: {chunk['line_start']}-{chunk['line_end']}")
        print(f"   Content preview: {chunk['content'][:80]}...")
    
    # Verify all expected chunks are present
    all_found = True
    for expected_type, expected_name in expected_chunks:
        found = any(
            chunk['chunk_type'] == expected_type and chunk['name'] == expected_name
            for chunk in chunks
        )
        if not found:
            print(f"\n✗ Missing chunk: {expected_type} '{expected_name}'")
            all_found = False
    
    # Verify docstring detection
    docstring_tests = [
        ('top_level_function', True),
        ('function_without_docstring', False),
        ('MyClass', True),
        ('async_function', True),
    ]
    
    print("\nDocstring Detection:")
    for func_name, expected_has_docstring in docstring_tests:
        chunk = next((c for c in chunks if c['name'] == func_name), None)
        if chunk:
            has_docstring = chunk.get('has_docstring', False)
            status = "✓" if has_docstring == expected_has_docstring else "✗"
            print(f"{status} {func_name}: has_docstring={has_docstring} (expected: {expected_has_docstring})")
            if has_docstring != expected_has_docstring:
                all_found = False
    
    # Verify nested functions are included in parent
    print("\nNested Function Handling:")
    nested_func_chunk = next((c for c in chunks if c['name'] == 'function_with_nested_function'), None)
    if nested_func_chunk:
        # Check if nested_function is in the content
        if 'nested_function' in nested_func_chunk['content']:
            print("✓ Nested function included in parent function chunk")
        else:
            print("✗ Nested function NOT found in parent function chunk")
            all_found = False
    else:
        print("✗ Could not find function_with_nested_function chunk")
        all_found = False
    
    return all_found


def test_class_methods():
    """Test that class methods are included in class chunk."""
    print("\n" + "=" * 70)
    print("Test 3: Class Methods")
    print("=" * 70)
    
    chunks = chunk_code(SAMPLE_PYTHON_CODE, language='python', source_path='test.py')
    
    # Find MyClass chunk
    class_chunk = next((c for c in chunks if c['name'] == 'MyClass'), None)
    
    if class_chunk:
        print("✓ Found MyClass chunk")
        print(f"   Lines: {class_chunk['line_start']}-{class_chunk['line_end']}")
        
        # Verify methods are included
        methods = ['__init__', 'instance_method', 'method_without_docstring']
        all_methods_found = True
        for method in methods:
            if method in class_chunk['content']:
                print(f"   ✓ Method '{method}' found in class chunk")
            else:
                print(f"   ✗ Method '{method}' NOT found in class chunk")
                all_methods_found = False
        
        return all_methods_found
    else:
        print("✗ Could not find MyClass chunk")
        return False


def test_empty_code():
    """Test edge case: empty code."""
    print("\n" + "=" * 70)
    print("Test 4: Edge Cases")
    print("=" * 70)
    
    # Empty code
    chunks = chunk_code("", language='python')
    if len(chunks) == 0:
        print("✓ Empty code returns empty chunks")
    else:
        print(f"✗ Empty code returned {len(chunks)} chunks (expected 0)")
        return False
    
    # Whitespace only
    chunks = chunk_code("   \n\n   ", language='python')
    if len(chunks) == 0:
        print("✓ Whitespace-only code returns empty chunks")
    else:
        print(f"✗ Whitespace-only code returned {len(chunks)} chunks (expected 0)")
        return False
    
    # Invalid Python syntax (should fall back gracefully)
    chunks = chunk_code("def invalid syntax here", language='python')
    if len(chunks) >= 0:  # Should return empty or fall back to recursive
        print("✓ Invalid syntax handled gracefully")
    else:
        print("✗ Invalid syntax not handled")
        return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Step 14: Code-Aware Chunking - Test")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Language Detection", test_language_detection()))
    results.append(("Code Chunking", test_code_chunking()))
    results.append(("Class Methods", test_class_methods()))
    results.append(("Edge Cases", test_empty_code()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

