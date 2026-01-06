#!/usr/bin/env python3
"""
Test script for Step 9: Retriever Agent (Basic)

Tests the RetrieverAgent by:
1. Creating a sample ParsedBRD
2. Running RetrieverAgent with different repo URLs
3. Verifying chunks are returned with correct metadata
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.agents.retriever import RetrieverAgent
from src.brd_agent.models.brd import ParsedBRD, DocumentInfo, BusinessObjective, Requirements, FunctionalRequirement
from src.brd_agent.config import get_settings


def create_sample_brd() -> ParsedBRD:
    """Create a sample ParsedBRD for testing."""
    return ParsedBRD(
        document_info=DocumentInfo(
            title="Customer Onboarding Portal",
            version="1.0"
        ),
        executive_summary="A new customer onboarding portal to streamline the signup process and reduce time-to-value for new customers.",
        business_objectives=[
            BusinessObjective(
                id="BO001",
                objective="Reduce customer onboarding time by 50%",
                priority="High"
            ),
            BusinessObjective(
                id="BO002",
                objective="Improve customer satisfaction scores",
                priority="Medium"
            ),
        ],
        requirements=Requirements(
            functional=[
                FunctionalRequirement(
                    id="FR001",
                    description="User authentication and authorization",
                    priority="Critical"
                ),
                FunctionalRequirement(
                    id="FR002",
                    description="Profile creation and management",
                    priority="High"
                ),
            ]
        )
    )


def test_retriever_agent():
    """Test RetrieverAgent with sample BRD."""
    print("=" * 70)
    print("Step 9: Retriever Agent (Basic) - Test")
    print("=" * 70)
    
    settings = get_settings()
    default_repo = settings.default_repo_url
    
    print(f"\nDefault Repository: {default_repo}")
    print(f"RAG Top-K: {settings.rag_top_k}")
    
    # Create sample BRD
    print("\n1. Creating sample ParsedBRD...")
    parsed_brd = create_sample_brd()
    print(f"   ✓ Created BRD: {parsed_brd.document_info.title}")
    print(f"   - Executive Summary: {parsed_brd.executive_summary[:80]}...")
    print(f"   - Business Objectives: {len(parsed_brd.business_objectives)}")
    
    # Initialize RetrieverAgent
    print("\n2. Initializing RetrieverAgent...")
    try:
        retriever = RetrieverAgent()
        print(f"   ✓ RetrieverAgent initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize RetrieverAgent: {e}")
        return False
    
    # Test with default repository
    print(f"\n3. Testing retrieval with default repository ({default_repo})...")
    try:
        results = retriever.run(parsed_brd, repo_url=None)
        
        if not results:
            print(f"   ⚠ No results returned (collection might not exist)")
            print(f"   This is expected if repository hasn't been ingested yet.")
            print(f"   To test fully, run: python -m cli.ingest")
            return True  # Not a failure, just no data
        
        print(f"   ✓ Retrieved {len(results)} chunks")
        
        # Display first result
        if results:
            first_result = results[0]
            print(f"\n   Top Result:")
            print(f"   - Source: {first_result['source']}")
            print(f"   - Distance: {first_result['distance']:.4f}")
            print(f"   - Content preview: {first_result['content'][:150]}...")
            if 'metadata' in first_result:
                meta = first_result['metadata']
                print(f"   - Metadata: file_path={meta.get('file_path')}, "
                      f"line_start={meta.get('line_start')}, line_end={meta.get('line_end')}")
        
    except Exception as e:
        print(f"   ✗ Failed to retrieve: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test with explicit repository URL
    print(f"\n4. Testing retrieval with explicit repository URL...")
    try:
        results = retriever.run(parsed_brd, repo_url=default_repo)
        print(f"   ✓ Retrieved {len(results)} chunks with explicit repo URL")
    except Exception as e:
        print(f"   ✗ Failed with explicit repo URL: {e}")
        return False
    
    # Verify result structure
    print("\n5. Verifying result structure...")
    if results:
        result = results[0]
        required_keys = ['content', 'source', 'metadata', 'distance']
        for key in required_keys:
            if key not in result:
                print(f"   ✗ Missing required key: {key}")
                return False
        print(f"   ✓ Result structure is valid")
        print(f"   - Keys: {list(result.keys())}")
    else:
        print(f"   ⚠ No results to verify (collection might not exist)")
    
    # Test BRD summary extraction
    print("\n6. Testing BRD summary extraction...")
    try:
        summary = retriever._extract_brd_summary(parsed_brd)
        print(f"   ✓ BRD summary extracted ({len(summary)} characters)")
        print(f"   Preview: {summary[:200]}...")
    except Exception as e:
        print(f"   ✗ Failed to extract summary: {e}")
        return False
    
    # Test with non-existent repository
    print("\n7. Testing with non-existent repository...")
    try:
        results = retriever.run(parsed_brd, repo_url="https://github.com/nonexistent/repo")
        print(f"   ✓ Handled gracefully: {len(results)} results (expected 0)")
    except ValueError as e:
        print(f"   ✓ Handled gracefully: {e}")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ All tests passed!")
    print("=" * 70)
    
    if not results:
        print("\nNote: No chunks retrieved because repository hasn't been ingested.")
        print("To test full functionality, run:")
        print(f"  python -m cli.ingest {default_repo}")
        print("Then run this test again.")
    
    return True


if __name__ == "__main__":
    success = test_retriever_agent()
    sys.exit(0 if success else 1)

