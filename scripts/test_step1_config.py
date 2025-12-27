#!/usr/bin/env python3
"""
Test script for Step 1: Configuration Setup
Verifies that RAG configuration loads correctly and can be overridden via environment variables.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.config import get_settings, reload_settings


def test_config_loading():
    """Test that configuration loads without errors"""
    print("🧪 Test 1: Configuration Loading")
    print("-" * 50)
    
    try:
        settings = get_settings()
        print("✅ Configuration loaded successfully")
        print(f"   Settings object: {type(settings).__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False


def test_default_values():
    """Test that all configuration values have appropriate defaults"""
    print("\n🧪 Test 2: Default Values")
    print("-" * 50)
    
    settings = get_settings()
    
    # Check all RAG config fields have defaults
    checks = [
        ("chromadb_path", settings.chromadb_path, "./.chromadb"),
        ("ollama_embedding_url", settings.ollama_embedding_url, "http://localhost:11434"),
        ("ollama_embedding_model", settings.ollama_embedding_model, "nomic-embed-text"),
        ("rag_enabled", settings.rag_enabled, False),
        ("default_repo_url", settings.default_repo_url, "https://github.com/paperless-ngx/paperless-ngx"),
        ("rag_top_k", settings.rag_top_k, 5),
        ("rag_query_count", settings.rag_query_count, 3),
    ]
    
    all_passed = True
    for name, actual, expected in checks:
        if actual == expected:
            print(f"✅ {name}: {actual}")
        else:
            print(f"❌ {name}: Expected {expected}, got {actual}")
            all_passed = False
    
    return all_passed


def test_env_override():
    """Test that default_repo_url can be overridden via DEFAULT_REPO_URL environment variable"""
    print("\n🧪 Test 3: Environment Variable Override")
    print("-" * 50)
    
    # Set test environment variable
    test_repo_url = "https://github.com/test-owner/test-repo"
    os.environ["DEFAULT_REPO_URL"] = test_repo_url
    
    # Reload settings to pick up new env var
    settings = reload_settings()
    
    if settings.default_repo_url == test_repo_url:
        print(f"✅ default_repo_url overridden successfully: {settings.default_repo_url}")
        # Clean up
        del os.environ["DEFAULT_REPO_URL"]
        reload_settings()
        return True
    else:
        print(f"❌ Failed to override: Expected {test_repo_url}, got {settings.default_repo_url}")
        # Clean up
        del os.environ["DEFAULT_REPO_URL"]
        reload_settings()
        return False


def test_config_types():
    """Test that configuration values have correct types"""
    print("\n🧪 Test 4: Configuration Types")
    print("-" * 50)
    
    settings = get_settings()
    
    checks = [
        ("chromadb_path", settings.chromadb_path, str),
        ("ollama_embedding_url", settings.ollama_embedding_url, str),
        ("ollama_embedding_model", settings.ollama_embedding_model, str),
        ("rag_enabled", settings.rag_enabled, bool),
        ("default_repo_url", settings.default_repo_url, str),
        ("rag_top_k", settings.rag_top_k, int),
        ("rag_query_count", settings.rag_query_count, int),
    ]
    
    all_passed = True
    for name, value, expected_type in checks:
        if isinstance(value, expected_type):
            print(f"✅ {name}: {type(value).__name__}")
        else:
            print(f"❌ {name}: Expected {expected_type.__name__}, got {type(value).__name__}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("=" * 50)
    print("Step 1 Configuration Test Suite")
    print("=" * 50)
    
    results = [
        test_config_loading(),
        test_default_values(),
        test_env_override(),
        test_config_types(),
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

