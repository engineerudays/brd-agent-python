#!/usr/bin/env python3
"""
Test script for Step 7: End-to-End Ingestion (Manual Test)

Tests the complete ingestion pipeline:
1. Fetch README.md from paperless-ngx via GitHubClient
2. Load via MarkdownLoader
3. Chunk via chunking service
4. Generate embeddings via EmbeddingService
5. Store in ChromaDB via VectorStore
6. Query and verify retrieval works
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.github_client import GitHubClient
from src.brd_agent.services.document_loaders import load_markdown
from src.brd_agent.services.chunking import chunk_markdown
from src.brd_agent.services.embeddings import EmbeddingService
from src.brd_agent.services.vector_store import VectorStore
from src.brd_agent.config import get_settings


def test_end_to_end_ingestion():
    """Test the complete ingestion pipeline."""
    print("=" * 70)
    print("Step 7: End-to-End Ingestion Pipeline - Test")
    print("=" * 70)
    
    settings = get_settings()
    repo_url = settings.default_repo_url
    
    print(f"\nRepository: {repo_url}")
    print(f"ChromaDB Path: {settings.chromadb_path}")
    print(f"Ollama URL: {settings.ollama_embedding_url}")
    print(f"Embedding Model: {settings.ollama_embedding_model}")
    
    # Step 1: Fetch README.md from GitHub
    print("\n" + "-" * 70)
    print("Step 1: Fetching README.md from GitHub...")
    print("-" * 70)
    
    try:
        github_client = GitHubClient()
        readme_content = github_client.get_file_content(repo_url, "README.md")
        print(f"✓ Successfully fetched README.md ({len(readme_content)} characters)")
    except Exception as e:
        print(f"✗ Failed to fetch README.md: {e}")
        return False
    
    # Step 2: Load markdown document
    print("\n" + "-" * 70)
    print("Step 2: Loading markdown document...")
    print("-" * 70)
    
    try:
        doc = load_markdown(readme_content, "README.md")
        print(f"✓ Successfully loaded markdown document")
        print(f"  - Source: {doc.source_path}")
        print(f"  - Type: {doc.doc_type}")
        print(f"  - Lines: {doc.metadata['line_count']}")
        print(f"  - Words: {doc.metadata['word_count']}")
        print(f"  - Headers: {doc.metadata['header_count']}")
        if 'title' in doc.metadata:
            print(f"  - Title: {doc.metadata['title']}")
    except Exception as e:
        print(f"✗ Failed to load markdown: {e}")
        return False
    
    # Step 3: Chunk the document
    print("\n" + "-" * 70)
    print("Step 3: Chunking document...")
    print("-" * 70)
    
    try:
        chunks = chunk_markdown(doc.content, doc.source_path)
        print(f"✓ Successfully chunked document into {len(chunks)} chunks")
        
        # Display chunk summary
        for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
            preview = chunk['content'][:80].replace('\n', ' ')
            print(f"  Chunk {i}: Lines {chunk['line_start']}-{chunk['line_end']} ({len(chunk['content'])} chars)")
            print(f"    Preview: {preview}...")
        
        if len(chunks) > 3:
            print(f"  ... and {len(chunks) - 3} more chunks")
            
    except Exception as e:
        print(f"✗ Failed to chunk document: {e}")
        return False
    
    # Step 4: Generate embeddings
    print("\n" + "-" * 70)
    print("Step 4: Generating embeddings...")
    print("-" * 70)
    
    try:
        embedding_service = EmbeddingService()
        print(f"✓ EmbeddingService initialized")
        
        # Generate embeddings for all chunks
        print(f"  Generating embeddings for {len(chunks)} chunks...")
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)
        
        print(f"✓ Successfully generated {len(embeddings)} embeddings")
        print(f"  - Embedding dimension: {len(embeddings[0])}")
        
    except Exception as e:
        print(f"✗ Failed to generate embeddings: {e}")
        print(f"  Make sure Ollama is running and '{settings.ollama_embedding_model}' model is available")
        return False
    
    # Step 5: Store in ChromaDB
    print("\n" + "-" * 70)
    print("Step 5: Storing in ChromaDB...")
    print("-" * 70)
    
    try:
        vector_store = VectorStore()
        print(f"✓ VectorStore initialized")
        
        # Prepare metadata for each chunk
        timestamp = datetime.utcnow().isoformat()
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                "repo": repo_url,
                "file_path": chunk['source'],
                "doc_type": "markdown",
                "chunk_type": chunk['chunk_type'],
                "line_start": chunk['line_start'],
                "line_end": chunk['line_end'],
                "chunk_index": i,
                "timestamp": timestamp,
            }
            metadatas.append(metadata)
            ids.append(f"{doc.source_path}_chunk_{i}")
        
        # Add documents to vector store
        vector_store.add_documents(
            repo_url=repo_url,
            documents=chunk_texts,
            embeddings=embeddings,
            metadata=metadatas,
        )
        
        print(f"✓ Successfully stored {len(chunks)} chunks in ChromaDB")
        print(f"  - Collection: {vector_store.get_collection_name(repo_url)}")
        
        # Verify collection exists and has documents
        collection = vector_store.get_collection(repo_url)
        if collection:
            count = collection.count()
            print(f"  - Collection document count: {count}")
        
    except Exception as e:
        print(f"✗ Failed to store in ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Query and verify retrieval
    print("\n" + "-" * 70)
    print("Step 6: Querying and verifying retrieval...")
    print("-" * 70)
    
    try:
        # Test query 1: General query about the project
        test_queries = [
            "What is paperless-ngx?",
            "How to install paperless?",
            "Docker deployment",
        ]
        
        for query_text in test_queries:
            print(f"\n  Query: '{query_text}'")
            
            # Generate query embedding
            query_embedding = embedding_service.embed(query_text)
            
            # Query vector store
            results = vector_store.query(
                repo_url=repo_url,
                query_embedding=query_embedding,
                top_k=3,
            )
            
            # ChromaDB returns nested lists: results['documents'][0] is the list of documents
            if results and 'documents' in results and results['documents'] and len(results['documents'][0]) > 0:
                doc_list = results['documents'][0]
                metadata_list = results['metadatas'][0] if results['metadatas'] and results['metadatas'][0] else []
                distance_list = results['distances'][0] if results['distances'] and results['distances'][0] else []
                
                print(f"    ✓ Found {len(doc_list)} results")
                
                # Show top result
                top_doc = doc_list[0]
                top_metadata = metadata_list[0] if metadata_list else {}
                top_distance = distance_list[0] if distance_list else None
                
                preview = top_doc[:150].replace('\n', ' ')
                print(f"    Top result (distance: {top_distance:.4f}):")
                print(f"      Source: {top_metadata.get('file_path', 'unknown')}")
                print(f"      Lines: {top_metadata.get('line_start', '?')}-{top_metadata.get('line_end', '?')}")
                print(f"      Preview: {preview}...")
            else:
                print(f"    ✗ No results found")
                print(f"    Results structure: {results}")
                return False
        
        print("\n  ✓ All queries returned relevant results")
        
    except Exception as e:
        print(f"✗ Failed to query vector store: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ End-to-End Ingestion Test PASSED!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  - Document: README.md from {repo_url}")
    print(f"  - Chunks created: {len(chunks)}")
    print(f"  - Embeddings generated: {len(embeddings)}")
    print(f"  - Stored in ChromaDB: ✓")
    print(f"  - Retrieval verified: ✓")
    print(f"\nThe ingestion pipeline is working correctly!")
    
    return True


if __name__ == "__main__":
    success = test_end_to_end_ingestion()
    sys.exit(0 if success else 1)

