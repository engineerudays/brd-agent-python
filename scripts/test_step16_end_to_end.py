#!/usr/bin/env python3
"""
Test script for Step 16: End-to-End Testing

Full system test with paperless-ngx:
1. Check if collection exists (avoid GitHub API calls)
2. Load sample BRD
3. Run workflow with RAG enabled
4. Verify context retrieval
5. Verify Django/Python patterns in plan
6. Save artifacts and generate report
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from src.brd_agent.graph.workflow import BRDWorkflow
from src.brd_agent.services.vector_store import VectorStore
from src.brd_agent.config import get_settings

console = Console()

# Output directory
OUTPUT_DIR = project_root / "sample_inputs" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def check_collection_exists(repo_url: str) -> tuple[bool, int]:
    """
    Check if ChromaDB collection exists for repository.
    
    Returns:
        (exists: bool, document_count: int)
    """
    try:
        vector_store = VectorStore()
        collection = vector_store.get_collection(repo_url)
        
        if collection is None:
            return False, 0
        
        doc_count = collection.count()
        return True, doc_count
    except Exception as e:
        console.print(f"[yellow]⚠ Error checking collection: {e}[/yellow]")
        return False, 0


def load_sample_brd() -> Dict[str, Any]:
    """Load sample BRD for paperless-ngx feature."""
    brd_path = project_root / "sample_inputs" / "brds" / "step-16-e2e-test-paperless_ngx_feature.json"
    
    if not brd_path.exists():
        raise FileNotFoundError(f"Sample BRD not found: {brd_path}")
    
    with open(brd_path, 'r') as f:
        return json.load(f)


def verify_django_patterns(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that plan references Django/Python patterns.
    
    Returns:
        Dictionary with verification results
    """
    verification = {
        "django_mentioned": False,
        "python_mentioned": False,
        "django_rest_framework": False,
        "django_models": False,
        "django_views": False,
        "tech_stack_aligned": False,
        "patterns_found": []
    }
    
    # Convert plan to string for searching
    plan_str = json.dumps(plan, default=str).lower()
    
    # Check for Django patterns
    django_keywords = [
        "django",
        "django rest framework",
        "django rest",
        "drf",
        "django models",
        "django views",
        "django orm",
        "django admin",
    ]
    
    python_keywords = [
        "python",
        "python web",
        "python framework",
    ]
    
    for keyword in django_keywords:
        if keyword in plan_str:
            verification["django_mentioned"] = True
            verification["patterns_found"].append(keyword)
            if "rest" in keyword or "drf" in keyword:
                verification["django_rest_framework"] = True
            if "model" in keyword:
                verification["django_models"] = True
            if "view" in keyword:
                verification["django_views"] = True
    
    for keyword in python_keywords:
        if keyword in plan_str:
            verification["python_mentioned"] = True
            verification["patterns_found"].append(keyword)
    
    # Check tech stack alignment
    # Look for Django-specific technologies vs generic ones
    generic_frameworks = ["flask", "fastapi", "express", "spring", "rails"]
    django_found = verification["django_mentioned"]
    generic_found = any(fw in plan_str for fw in generic_frameworks)
    
    verification["tech_stack_aligned"] = django_found and not generic_found
    
    return verification


def analyze_plan_content(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze plan content for verification."""
    analysis = {
        "features_count": 0,
        "phases_count": 0,
        "technologies": [],
        "architecture_components": [],
        "has_rag_context": False,
        "source_citations": []
    }
    
    # Extract from engineering plan
    ep = plan.get("engineering_plan", {})
    
    # Features
    features = ep.get("feature_breakdown", [])
    analysis["features_count"] = len(features)
    
    # Phases
    phases = ep.get("implementation_phases", [])
    analysis["phases_count"] = len(phases)
    
    # Technologies
    resources = ep.get("resource_requirements", {})
    technologies = resources.get("tools_and_technologies", [])
    analysis["technologies"] = technologies[:10]  # Top 10
    
    # Architecture
    arch = ep.get("technical_architecture", {})
    components = arch.get("system_components", [])
    analysis["architecture_components"] = components[:10]  # Top 10
    
    # RAG context
    metadata = plan.get("metadata", {})
    rag_context = metadata.get("rag_context", {})
    analysis["has_rag_context"] = rag_context.get("enabled", False)
    analysis["source_citations"] = rag_context.get("source_files", [])
    
    return analysis


def generate_markdown_report(
    test_results: Dict[str, Any],
    verification: Dict[str, Any],
    plan_analysis: Dict[str, Any]
) -> str:
    """Generate formatted markdown verification report."""
    
    report = f"""# Step 16: End-to-End Testing - Verification Report

## Test Overview

**Repository**: {test_results.get('repo_url', 'N/A')}  
**BRD**: {test_results.get('brd_name', 'N/A')}  
**Test Date**: {test_results.get('timestamp', 'N/A')}  
**Status**: {test_results.get('status', 'unknown')}

---

## 1. Collection Status

- **Collection Exists**: {'✅ Yes' if test_results.get('collection_exists') else '❌ No'}
- **Document Count**: {test_results.get('document_count', 0)}
- **Collection Name**: {test_results.get('collection_name', 'N/A')}

---

## 2. Workflow Execution

### Stages Completed
"""
    
    stages = test_results.get('stages_completed', [])
    for stage in stages:
        report += f"- ✅ {stage}\n"
    
    report += f"""
### Context Retrieval

- **RAG Enabled**: {'✅ Yes' if test_results.get('rag_enabled') else '❌ No'}
- **Context Retrieved**: {'✅ Yes' if test_results.get('context_retrieved') else '❌ No'}
- **Chunks Retrieved**: {test_results.get('chunks_retrieved', 0)}
- **Source Files**: {len(test_results.get('source_files', []))}

**Source Files Used:**
"""
    
    for source in test_results.get('source_files', [])[:10]:
        report += f"- `{source}`\n"
    
    report += f"""
---

## 3. Plan Verification

### Django/Python Pattern Detection

- **Django Mentioned**: {'✅ Yes' if verification.get('django_mentioned') else '❌ No'}
- **Python Mentioned**: {'✅ Yes' if verification.get('python_mentioned') else '❌ No'}
- **Django REST Framework**: {'✅ Yes' if verification.get('django_rest_framework') else '❌ No'}
- **Django Models**: {'✅ Yes' if verification.get('django_models') else '❌ No'}
- **Django Views**: {'✅ Yes' if verification.get('django_views') else '❌ No'}
- **Tech Stack Aligned**: {'✅ Yes' if verification.get('tech_stack_aligned') else '❌ No'}

**Patterns Found:**
"""
    
    for pattern in verification.get('patterns_found', []):
        report += f"- `{pattern}`\n"
    
    report += f"""
### Plan Content Analysis

- **Features Generated**: {plan_analysis.get('features_count', 0)}
- **Implementation Phases**: {plan_analysis.get('phases_count', 0)}
- **RAG Context Used**: {'✅ Yes' if plan_analysis.get('has_rag_context') else '❌ No'}

**Technologies Recommended:**
"""
    
    for tech in plan_analysis.get('technologies', [])[:10]:
        report += f"- {tech}\n"
    
    report += f"""
**Architecture Components:**
"""
    
    for component in plan_analysis.get('architecture_components', [])[:10]:
        report += f"- {component}\n"
    
    report += f"""
---

## 4. Verification Summary

### ✅ Passed Checks

"""
    
    checks_passed = []
    checks_failed = []
    
    if test_results.get('collection_exists'):
        checks_passed.append("Collection exists in ChromaDB")
    else:
        checks_failed.append("Collection does not exist")
    
    if test_results.get('context_retrieved'):
        checks_passed.append("Context retrieved from RAG")
    else:
        checks_failed.append("Context not retrieved")
    
    if verification.get('django_mentioned'):
        checks_passed.append("Django patterns found in plan")
    else:
        checks_failed.append("Django patterns not found")
    
    if verification.get('tech_stack_aligned'):
        checks_passed.append("Tech stack aligned with existing system")
    else:
        checks_failed.append("Tech stack may not be aligned")
    
    if plan_analysis.get('has_rag_context'):
        checks_passed.append("Plan includes RAG context metadata")
    else:
        checks_failed.append("Plan missing RAG context metadata")
    
    for check in checks_passed:
        report += f"- ✅ {check}\n"
    
    report += f"""
### ❌ Failed Checks

"""
    
    if checks_failed:
        for check in checks_failed:
            report += f"- ❌ {check}\n"
    else:
        report += "- None\n"
    
    report += f"""
---

## 5. Conclusion

**Overall Status**: {'✅ PASSED' if len(checks_failed) == 0 else '⚠️ PARTIAL' if len(checks_passed) > len(checks_failed) else '❌ FAILED'}

**Key Findings:**
- RAG integration is {'working correctly' if test_results.get('context_retrieved') else 'not working'}
- Plan {'aligns with' if verification.get('tech_stack_aligned') else 'may not align with'} existing Django/Python architecture
- {'Source citations' if plan_analysis.get('has_rag_context') else 'No source citations'} included in plan metadata

**Recommendations:**
"""
    
    if not test_results.get('collection_exists'):
        report += "- Ingest paperless-ngx documentation before running workflow\n"
    
    if not verification.get('django_mentioned'):
        report += "- Review plan to ensure Django patterns are referenced\n"
    
    if not verification.get('tech_stack_aligned'):
        report += "- Verify plan uses Django instead of generic frameworks\n"
    
    if len(checks_failed) == 0:
        report += "- All checks passed! RAG integration is working correctly.\n"
    
    report += f"""
---

## 6. Artifacts

All artifacts have been saved to `sample_inputs/outputs/`:
- `step-16-e2e-test-engineering_plan.json` - Full engineering plan
- `step-16-e2e-test-project_schedule.json` - Full project schedule
- `step-16-e2e-test-test_results.json` - Complete test results
- `step-16-e2e-test-verification_report.md` - This report

---
*Generated by Step 16 End-to-End Test*
"""
    
    return report


def main():
    """Run end-to-end test."""
    console.print("\n[bold blue]" + "=" * 70)
    console.print("[bold blue]Step 16: End-to-End Testing[/bold blue]")
    console.print("[bold blue]" + "=" * 70)
    
    settings = get_settings()
    repo_url = settings.default_repo_url
    
    # Enable RAG for this test (override config)
    settings.rag_enabled = True
    
    console.print(f"\n[bold]Repository:[/bold] {repo_url}")
    console.print(f"[bold]RAG Enabled:[/bold] {settings.rag_enabled} (enabled for test)")
    
    # Step 1: Check collection exists
    console.print("\n[bold yellow]Step 1: Checking Collection Status[/bold yellow]")
    collection_exists, doc_count = check_collection_exists(repo_url)
    
    if collection_exists:
        console.print(f"[green]✓[/green] Collection exists with {doc_count} documents")
    else:
        console.print("[red]✗[/red] Collection does not exist")
        console.print("\n[yellow]⚠ Collection not found. Please ingest paperless-ngx documentation first:[/yellow]")
        console.print(f"[dim]  python -m cli.ingest github {repo_url} --path docs/[/dim]")
        console.print("\n[bold]Proceeding with test anyway (RAG will be skipped)...[/bold]")
    
    # Step 2: Load sample BRD
    console.print("\n[bold yellow]Step 2: Loading Sample BRD[/bold yellow]")
    try:
        brd_data = load_sample_brd()
        brd_name = brd_data.get('project', {}).get('name', 'Unknown')
        console.print(f"[green]✓[/green] Loaded BRD: {brd_name}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load BRD: {e}")
        return 1
    
    # Step 3: Run workflow
    console.print("\n[bold yellow]Step 3: Running Workflow[/bold yellow]")
    console.print("[dim]This may take a few minutes...[/dim]")
    
    try:
        # Create workflow with RAG enabled
        workflow = BRDWorkflow()
        # Ensure RAG is enabled in workflow settings
        workflow.settings.rag_enabled = True
        result = workflow.run(brd_data)
        
        status = result.get("status", "unknown")
        console.print(f"[green]✓[/green] Workflow completed with status: {status}")
        
        stages = result.get("stages_completed", [])
        console.print(f"[green]✓[/green] Stages completed: {', '.join(stages)}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 4: Extract and verify results
    console.print("\n[bold yellow]Step 4: Verifying Results[/bold yellow]")
    
    engineering_plan = result.get("engineering_plan", {})
    project_schedule = result.get("project_schedule", {})
    retrieved_context = result.get("retrieved_context")
    
    # Check context retrieval
    context_retrieved = retrieved_context is not None and len(retrieved_context) > 0
    chunks_retrieved = len(retrieved_context) if retrieved_context else 0
    
    # Extract source files
    source_files = []
    if retrieved_context:
        source_files = list(set([
            chunk.get('source', 'unknown')
            for chunk in retrieved_context
            if chunk.get('source')
        ]))
    
    # Verify Django patterns
    verification = verify_django_patterns(engineering_plan)
    
    # Analyze plan
    plan_analysis = analyze_plan_content(engineering_plan)
    
    # Prepare test results
    test_results = {
        "repo_url": repo_url,
        "brd_name": brd_name,
        "status": status,
        "stages_completed": stages,
        "collection_exists": collection_exists,
        "document_count": doc_count,
        "collection_name": VectorStore().get_collection_name(repo_url) if collection_exists else None,
        "rag_enabled": settings.rag_enabled,
        "context_retrieved": context_retrieved,
        "chunks_retrieved": chunks_retrieved,
        "source_files": source_files,
        "timestamp": result.get("timestamp", ""),
    }
    
    # Step 5: Save artifacts
    console.print("\n[bold yellow]Step 5: Saving Artifacts[/bold yellow]")
    
    # Save engineering plan
    plan_file = OUTPUT_DIR / "step-16-e2e-test-engineering_plan.json"
    with open(plan_file, 'w') as f:
        json.dump(engineering_plan, f, indent=2)
    console.print(f"[green]✓[/green] Saved: {plan_file}")
    
    # Save project schedule
    schedule_file = OUTPUT_DIR / "step-16-e2e-test-project_schedule.json"
    with open(schedule_file, 'w') as f:
        json.dump(project_schedule, f, indent=2)
    console.print(f"[green]✓[/green] Saved: {schedule_file}")
    
    # Save test results
    results_file = OUTPUT_DIR / "step-16-e2e-test-test_results.json"
    full_results = {
        "test_results": test_results,
        "verification": verification,
        "plan_analysis": plan_analysis,
        "engineering_plan": engineering_plan,
        "project_schedule": project_schedule,
    }
    with open(results_file, 'w') as f:
        json.dump(full_results, f, indent=2)
    console.print(f"[green]✓[/green] Saved: {results_file}")
    
    # Generate and save markdown report
    report_content = generate_markdown_report(test_results, verification, plan_analysis)
    report_file = OUTPUT_DIR / "step-16-e2e-test-verification_report.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    console.print(f"[green]✓[/green] Saved: {report_file}")
    
    # Step 6: Display summary
    console.print("\n[bold magenta]" + "=" * 70)
    console.print("[bold magenta]Verification Summary[/bold magenta]")
    console.print("=" * 70)
    
    table = Table(title="Verification Results", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    table.add_row(
        "Collection Exists",
        "✅" if collection_exists else "❌",
        f"{doc_count} documents" if collection_exists else "Not found"
    )
    
    table.add_row(
        "Context Retrieved",
        "✅" if context_retrieved else "❌",
        f"{chunks_retrieved} chunks" if context_retrieved else "No context"
    )
    
    table.add_row(
        "Django Patterns",
        "✅" if verification.get('django_mentioned') else "❌",
        f"{len(verification.get('patterns_found', []))} patterns found"
    )
    
    table.add_row(
        "Tech Stack Aligned",
        "✅" if verification.get('tech_stack_aligned') else "❌",
        "Django detected" if verification.get('tech_stack_aligned') else "May not align"
    )
    
    table.add_row(
        "RAG Metadata",
        "✅" if plan_analysis.get('has_rag_context') else "❌",
        f"{len(plan_analysis.get('source_citations', []))} sources" if plan_analysis.get('has_rag_context') else "Missing"
    )
    
    console.print(table)
    
    # Final status
    checks_passed = sum([
        collection_exists,
        context_retrieved,
        verification.get('django_mentioned', False),
        verification.get('tech_stack_aligned', False),
        plan_analysis.get('has_rag_context', False),
    ])
    
    console.print(f"\n[bold]Overall:[/bold] {checks_passed}/5 checks passed")
    
    if checks_passed == 5:
        console.print("\n[bold green]✅ All verification checks passed![/bold green]")
    elif checks_passed >= 3:
        console.print("\n[bold yellow]⚠ Some checks passed - review report for details[/bold yellow]")
    else:
        console.print("\n[bold red]❌ Most checks failed - review report for details[/bold red]")
    
    console.print(f"\n[bold]Artifacts saved to:[/bold] {OUTPUT_DIR}")
    console.print(f"[bold]Report:[/bold] {report_file}")
    
    return 0 if checks_passed >= 3 else 1


if __name__ == "__main__":
    sys.exit(main())

