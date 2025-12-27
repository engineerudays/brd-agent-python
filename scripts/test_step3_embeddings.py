#!/usr/bin/env python3
"""
Test script for Step 3: Ollama Embedding Service
Verifies that EmbeddingService can generate embeddings using Ollama API.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.embeddings import EmbeddingService


def test_embedding_service_init():
    """Test that EmbeddingService initializes correctly"""
    print("🧪 Test 1: EmbeddingService Initialization")
    print("-" * 50)
    
    try:
        emb = EmbeddingService()
        print(f"✅ EmbeddingService initialized")
        print(f"   Ollama URL: {emb.ollama_url}")
        print(f"   Model: {emb.model_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False


def test_single_embedding():
    """Test generating embedding for a single text"""
    print("\n🧪 Test 2: Single Embedding Generation")
    print("-" * 50)
    
    try:
        emb = EmbeddingService()
        text = "This is a test document about Python programming."
        
        vector = emb.embed(text)
        
        # Verify embedding properties
        if not isinstance(vector, list):
            print(f"❌ Expected list, got {type(vector)}")
            return False
        
        if len(vector) != 768:
            print(f"❌ Expected dimension 768, got {len(vector)}")
            return False
        
        # Check that all values are floats
        if not all(isinstance(x, (int, float)) for x in vector):
            print(f"❌ Not all values are numeric")
            return False
        
        print(f"✅ Generated embedding: dimension {len(vector)}")
        print(f"   First few values: {vector[:5]}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        print(f"   Make sure Ollama is running with nomic-embed-text model")
        print(f"   Run: ollama pull nomic-embed-text")
        return False


def test_batch_embeddings():
    """Test generating embeddings for multiple texts"""
    print("\n🧪 Test 3: Batch Embedding Generation")
    print("-" * 50)
    
    try:
        emb = EmbeddingService()
        texts = [
            "This is a test document about Python programming.",
            "This document discusses machine learning and AI.",
            "This is about web development with FastAPI.",
        ]
        
        embeddings = emb.embed_batch(texts)
        
        # Verify batch results
        if len(embeddings) != len(texts):
            print(f"❌ Expected {len(texts)} embeddings, got {len(embeddings)}")
            return False
        
        # Verify each embedding
        for i, embedding in enumerate(embeddings):
            if len(embedding) != 768:
                print(f"❌ Embedding {i} has wrong dimension: {len(embedding)}")
                return False
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   All embeddings have dimension 768")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate batch embeddings: {e}")
        return False


def test_model_info():
    """Test getting model information"""
    print("\n🧪 Test 4: Model Info")
    print("-" * 50)
    
    try:
        emb = EmbeddingService()
        info = emb.get_model_info()
        
        required_keys = ["model_name", "ollama_url", "dimension"]
        for key in required_keys:
            if key not in info:
                print(f"❌ Missing key in model info: {key}")
                return False
        
        if info["dimension"] != 768:
            print(f"❌ Expected dimension 768, got {info['dimension']}")
            return False
        
        print(f"✅ Model info retrieved:")
        print(f"   Model: {info['model_name']}")
        print(f"   URL: {info['ollama_url']}")
        print(f"   Dimension: {info['dimension']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to get model info: {e}")
        return False


def test_empty_text_handling():
    """Test that empty text raises ValueError"""
    print("\n🧪 Test 5: Empty Text Handling")
    print("-" * 50)
    
    try:
        emb = EmbeddingService()
        
        # Test empty string
        try:
            emb.embed("")
            print(f"❌ Should have raised ValueError for empty string")
            return False
        except ValueError:
            print(f"✅ Empty string correctly raises ValueError")
        
        # Test whitespace-only string
        try:
            emb.embed("   ")
            print(f"❌ Should have raised ValueError for whitespace-only string")
            return False
        except ValueError:
            print(f"✅ Whitespace-only string correctly raises ValueError")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_custom_config():
    """Test initialization with custom configuration"""
    print("\n🧪 Test 6: Custom Configuration")
    print("-" * 50)
    
    try:
        # Test with custom URL and model
        emb = EmbeddingService(
            ollama_url="http://localhost:11434",
            model_name="nomic-embed-text"
        )
        
        if emb.ollama_url != "http://localhost:11434":
            print(f"❌ Custom URL not set correctly")
            return False
        
        if emb.model_name != "nomic-embed-text":
            print(f"❌ Custom model name not set correctly")
            return False
        
        print(f"✅ Custom configuration works")
        return True
        
    except Exception as e:
        print(f"❌ Failed with custom config: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Step 3 Embedding Service Test Suite")
    print("=" * 50)
    print("\n⚠️  Prerequisites:")
    print("   - Ollama must be running locally")
    print("   - nomic-embed-text model must be installed")
    print("   - Run: ollama pull nomic-embed-text")
    print("=" * 50)
    
    results = [
        test_embedding_service_init(),
        test_single_embedding(),
        test_batch_embeddings(),
        test_model_info(),
        test_empty_text_handling(),
        test_custom_config(),
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
        print("\n💡 Troubleshooting:")
        print("   1. Check if Ollama is running: curl http://localhost:11434/api/tags")
        print("   2. Pull the model: ollama pull nomic-embed-text")
        print("   3. Test manually: curl http://localhost:11434/api/embeddings -d '{\"model\":\"nomic-embed-text\",\"prompt\":\"test\"}'")
        return 1


if __name__ == "__main__":
    sys.exit(main())

