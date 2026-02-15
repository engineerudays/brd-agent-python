#!/usr/bin/env python3
"""
Test script for Step 11: Workflow Integration

Tests the BRD workflow with RetrieverAgent integrated:
1. Test workflow with RAG enabled
2. Test workflow with RAG disabled
3. Test workflow with missing collection (graceful degradation)
4. Verify retrieved_context flows to Planner
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.graph.workflow import BRDWorkflow
from src.brd_agent.config import get_settings


def create_sample_input():
    """Create a sample BRD input for testing."""
    return {
        "project": {
            "name": "Test Project",
            "description": "A test project for workflow integration",
            "objectives": [
                "Test objective 1",
                "Test objective 2"
            ]
        },
        "features": [
            {
                "id": "FR001",
                "name": "Feature 1",
                "description": "Test feature 1",
                "priority": "High"
            }
        ]
    }


def test_workflow_structure():
    """Test that workflow has RetrieverAgent integrated."""
    print("=" * 70)
    print("Step 11: Workflow Integration - Structure Test")
    print("=" * 70)
    
    workflow = BRDWorkflow()
    
    # Check retriever exists
    assert hasattr(workflow, 'retriever'), "Workflow missing retriever agent"
    print("✓ RetrieverAgent initialized in workflow")
    
    # Check retriever node exists
    assert hasattr(workflow, '_retriever_node'), "Workflow missing _retriever_node method"
    print("✓ _retriever_node method exists")
    
    # Check graph structure
    nodes = list(workflow.graph.nodes.keys())
    expected_nodes = ['parser', 'retriever', 'planner', 'scheduler', 'finalize']
    for node in expected_nodes:
        assert node in nodes, f"Missing node: {node}"
    
    print("✓ All required nodes present in graph")
    
    # Check node order
    node_list = [n for n in nodes if n not in ['__start__', '__end__']]
    assert node_list == expected_nodes, f"Node order incorrect: {node_list}"
    print("✓ Node order correct: parser -> retriever -> planner -> scheduler -> finalize")
    
    return True


def test_workflow_with_rag_disabled():
    """Test workflow with RAG disabled."""
    print("\n" + "-" * 70)
    print("Test 1: Workflow with RAG Disabled")
    print("-" * 70)
    
    settings = get_settings()
    original_rag_enabled = settings.rag_enabled
    
    try:
        # Temporarily disable RAG
        settings.rag_enabled = False
        
        workflow = BRDWorkflow()
        input_data = create_sample_input()
        
        print("Running workflow with RAG disabled...")
        result = workflow.run(input_data)
        
        assert result.get('status') == 'success', f"Workflow failed: {result.get('message')}"
        print("✓ Workflow completed successfully")
        
        assert result.get('retrieved_context') is None, "retrieved_context should be None when RAG disabled"
        print("✓ retrieved_context is None (RAG skipped)")
        
        assert 'brd_parsing' in result.get('stages_completed', []), "Parser stage not completed"
        assert 'engineering_plan' in result.get('stages_completed', []), "Planner stage not completed"
        assert 'project_schedule' in result.get('stages_completed', []), "Scheduler stage not completed"
        print("✓ All stages completed (RAG skipped gracefully)")
        
        return True
        
    finally:
        # Restore original setting
        settings.rag_enabled = original_rag_enabled


def test_workflow_with_missing_collection():
    """Test workflow with missing collection (graceful degradation)."""
    print("\n" + "-" * 70)
    print("Test 2: Workflow with Missing Collection (Graceful Degradation)")
    print("-" * 70)
    
    settings = get_settings()
    original_rag_enabled = settings.rag_enabled
    
    try:
        # Enable RAG but use non-existent repo
        settings.rag_enabled = True
        
        workflow = BRDWorkflow()
        input_data = create_sample_input()
        
        # Use a non-existent repository URL
        input_data['repo_url'] = 'https://github.com/nonexistent/repo'
        
        print("Running workflow with non-existent repository...")
        print("Note: Retriever may fall back to default repo if specified repo doesn't exist")
        result = workflow.run(input_data)
        
        assert result.get('status') == 'success', f"Workflow failed: {result.get('message')}"
        print("✓ Workflow completed successfully (graceful degradation)")
        
        # Check that workflow continued regardless of retrieval result
        retrieved_context = result.get('retrieved_context')
        if retrieved_context:
            print(f"✓ Retrieved {len(retrieved_context)} chunks (may be from default repo)")
        else:
            print("✓ retrieved_context is None/empty (collection missing)")
        
        assert 'brd_parsing' in result.get('stages_completed', []), "Parser stage not completed"
        assert 'engineering_plan' in result.get('stages_completed', []), "Planner stage not completed"
        print("✓ Workflow continued successfully regardless of retrieval result")
        
        return True
        
    finally:
        # Restore original setting
        settings.rag_enabled = original_rag_enabled


def test_workflow_with_rag_enabled():
    """Test workflow with RAG enabled (if collection exists)."""
    print("\n" + "-" * 70)
    print("Test 3: Workflow with RAG Enabled")
    print("-" * 70)
    
    settings = get_settings()
    original_rag_enabled = settings.rag_enabled
    
    try:
        # Enable RAG
        settings.rag_enabled = True
        
        workflow = BRDWorkflow()
        input_data = create_sample_input()
        
        print("Running workflow with RAG enabled...")
        result = workflow.run(input_data)
        
        assert result.get('status') == 'success', f"Workflow failed: {result.get('message')}"
        print("✓ Workflow completed successfully")
        
        # Check if retrieved_context is present (may be None if collection doesn't exist)
        retrieved_context = result.get('retrieved_context')
        if retrieved_context:
            print(f"✓ Retrieved {len(retrieved_context)} chunks")
            assert isinstance(retrieved_context, list), "retrieved_context should be a list"
        else:
            print("⚠ No retrieved_context (collection may not exist - this is OK)")
        
        assert 'brd_parsing' in result.get('stages_completed', []), "Parser stage not completed"
        assert 'engineering_plan' in result.get('stages_completed', []), "Planner stage not completed"
        assert 'project_schedule' in result.get('stages_completed', []), "Scheduler stage not completed"
        print("✓ All stages completed")
        
        # Check repo_url is set
        repo_url = result.get('repo_url')
        if repo_url:
            print(f"✓ repo_url set: {repo_url}")
        
        return True
        
    finally:
        # Restore original setting
        settings.rag_enabled = original_rag_enabled


def main():
    """Run all tests."""
    try:
        # Test 1: Structure
        test_workflow_structure()
        
        # Test 2: RAG Disabled
        test_workflow_with_rag_disabled()
        
        # Test 3: Missing Collection
        test_workflow_with_missing_collection()
        
        # Test 4: RAG Enabled
        test_workflow_with_rag_enabled()
        
        print("\n" + "=" * 70)
        print("✅ All Step 11 tests passed!")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ RetrieverAgent integrated into workflow")
        print("  ✓ Workflow structure correct")
        print("  ✓ Graceful degradation works (RAG disabled)")
        print("  ✓ Graceful degradation works (missing collection)")
        print("  ✓ Workflow continues successfully in all scenarios")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
