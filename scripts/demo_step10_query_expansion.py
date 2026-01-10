#!/usr/bin/env python3
"""
Demo script for Step 10: Query Expansion (Advanced Retrieval)

Demonstrates the improvement of query expansion over basic retrieval by:
1. Running basic retrieval (Step 9)
2. Running query expansion retrieval (Step 10)
3. Comparing results side-by-side
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel

from src.brd_agent.agents.retriever import RetrieverAgent
from src.brd_agent.models.brd import ParsedBRD
from src.brd_agent.config import get_settings

console = Console()


def load_sample_brd() -> ParsedBRD:
    """Load sample BRD for demonstration."""
    brd_path = project_root / "sample_inputs" / "brds" / "demo_step10_query_expansion.json"
    
    if not brd_path.exists():
        raise FileNotFoundError(f"Sample BRD not found: {brd_path}")
    
    with open(brd_path, 'r') as f:
        data = json.load(f)
    
    return ParsedBRD(**data)


def get_unique_sources(results: List[Dict[str, Any]]) -> set:
    """Get unique source files from results."""
    return {r['source'] for r in results}


def calculate_avg_distance(results: List[Dict[str, Any]]) -> float:
    """Calculate average distance score."""
    distances = [r['distance'] for r in results if r.get('distance') is not None]
    if not distances:
        return 0.0
    return sum(distances) / len(distances)


def main():
    """Run the query expansion demonstration."""
    console.print("\n[bold blue]=" * 70)
    console.print("[bold blue]Step 10: Query Expansion Demo[/bold blue]")
    console.print("[bold blue]=" * 70)
    
    settings = get_settings()
    repo_url = settings.default_repo_url
    
    console.print(f"\n[dim]Repository: {repo_url}[/dim]")
    console.print(f"[dim]RAG Top-K: {settings.rag_top_k}[/dim]")
    console.print(f"[dim]Query Count: {settings.rag_query_count}[/dim]")
    
    # Load sample BRD
    console.print("\n[bold]📄 Loading sample BRD...[/bold]")
    try:
        parsed_brd = load_sample_brd()
        console.print(f"[green]✓[/green] Loaded BRD: {parsed_brd.document_info.title}")
        console.print(f"   - Business Objectives: {len(parsed_brd.business_objectives)}")
        console.print(f"   - Functional Requirements: {len(parsed_brd.requirements.functional) if parsed_brd.requirements else 0}")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to load BRD: {e}[/bold red]")
        return 1
    
    # Initialize RetrieverAgent
    console.print("\n[bold]🤖 Initializing RetrieverAgent...[/bold]")
    try:
        retriever = RetrieverAgent()
        console.print("[green]✓[/green] RetrieverAgent initialized")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to initialize: {e}[/bold red]")
        return 1
    
    # Step 1: Basic Retrieval (Step 9)
    console.print("\n[bold yellow]" + "─" * 70)
    console.print("[bold yellow]Step 9: Basic Retrieval (Single Query)[/bold yellow]")
    console.print("[bold yellow]" + "─" * 70)
    
    try:
        basic_results = retriever.run(parsed_brd, repo_url=repo_url, use_query_expansion=False)
        console.print(f"[green]✓[/green] Retrieved {len(basic_results)} chunks")
        
        if basic_results:
            console.print(f"\n[bold]Single Query Used:[/bold]")
            brd_summary = retriever._extract_brd_summary(parsed_brd)
            console.print(f"  {brd_summary[:150]}...")
            
            console.print(f"\n[bold]Top Results:[/bold]")
            for i, result in enumerate(basic_results[:3], 1):
                console.print(f"  {i}. {result['source']} (distance: {result['distance']:.4f})")
        else:
            console.print("[yellow]⚠ No results found (collection might not exist)[/yellow]")
            console.print(f"   Run: python -m cli.ingest {repo_url}")
            return 0
            
    except Exception as e:
        console.print(f"[bold red]✗ Basic retrieval failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 2: Query Expansion Retrieval (Step 10)
    console.print("\n[bold green]" + "─" * 70)
    console.print("[bold green]Step 10: Query Expansion Retrieval[/bold green]")
    console.print("[bold green]" + "─" * 70)
    
    try:
        expanded_results = retriever.run(parsed_brd, repo_url=repo_url, use_query_expansion=True)
        console.print(f"[green]✓[/green] Retrieved {len(expanded_results)} chunks")
        
        # Show expanded queries
        # Note: We need to call the method directly to get queries before retrieval
        try:
            expanded_queries = retriever._generate_expanded_queries(parsed_brd)
            console.print(f"\n[bold]Expanded Queries Generated ({len(expanded_queries)}):[/bold]")
            for i, query in enumerate(expanded_queries, 1):
                console.print(f"  {i}. {query}")
            
            # Show BRD coverage
            num_objectives = len(parsed_brd.business_objectives) if parsed_brd.business_objectives else 0
            num_requirements = len(parsed_brd.requirements.functional) if parsed_brd.requirements and parsed_brd.requirements.functional else 0
            console.print(f"\n[dim]BRD Coverage: {num_objectives} objectives, {num_requirements} requirements[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠ Could not display queries: {e}[/yellow]")
        
        if expanded_results:
            console.print(f"\n[bold]Top Results:[/bold]")
            for i, result in enumerate(expanded_results[:3], 1):
                console.print(f"  {i}. {result['source']} (distance: {result['distance']:.4f})")
                
    except Exception as e:
        console.print(f"[bold red]✗ Query expansion retrieval failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Comparison
    console.print("\n[bold magenta]" + "─" * 70)
    console.print("[bold magenta]Comparison: Basic vs Query Expansion[/bold magenta]")
    console.print("[bold magenta]" + "─" * 70)
    
    # Calculate metrics
    basic_sources = get_unique_sources(basic_results)
    expanded_sources = get_unique_sources(expanded_results)
    
    basic_avg_dist = calculate_avg_distance(basic_results)
    expanded_avg_dist = calculate_avg_distance(expanded_results)
    
    # Find chunks in expanded but not in basic
    basic_content_hashes = {hash(r['content']) for r in basic_results}
    expanded_only = [
        r for r in expanded_results 
        if hash(r['content']) not in basic_content_hashes
    ]
    
    # Create comparison table
    table = Table(title="Retrieval Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="yellow")
    table.add_column("Basic Retrieval", style="red")
    table.add_column("Query Expansion", style="green")
    table.add_column("Improvement", style="magenta")
    
    table.add_row(
        "Number of Queries",
        "1",
        str(settings.rag_query_count),
        f"+{settings.rag_query_count - 1} queries"
    )
    
    table.add_row(
        "Total Chunks Retrieved",
        str(len(basic_results)),
        str(len(expanded_results)),
        f"+{len(expanded_results) - len(basic_results)} chunks"
    )
    
    table.add_row(
        "Unique Sources",
        str(len(basic_sources)),
        str(len(expanded_sources)),
        f"+{len(expanded_sources) - len(basic_sources)} sources"
    )
    
    table.add_row(
        "Average Distance",
        f"{basic_avg_dist:.4f}",
        f"{expanded_avg_dist:.4f}",
        f"{((basic_avg_dist - expanded_avg_dist) / basic_avg_dist * 100):.1f}% better" if basic_avg_dist > 0 else "N/A"
    )
    
    table.add_row(
        "Chunks Found Only by Expansion",
        "0",
        str(len(expanded_only)),
        f"+{len(expanded_only)} unique chunks"
    )
    
    console.print(table)
    
    # Show chunks found only by expansion
    if expanded_only:
        console.print(f"\n[bold green]✨ Chunks Found Only by Query Expansion:[/bold green]")
        for i, result in enumerate(expanded_only[:5], 1):
            console.print(f"  {i}. {result['source']}")
            console.print(f"     Distance: {result['distance']:.4f}")
            console.print(f"     Preview: {result['content'][:100]}...")
            console.print()
    
    # Summary
    console.print("\n[bold green]" + "=" * 70)
    console.print("[bold green]✅ Query Expansion Demo Complete![/bold green]")
    console.print("[bold green]" + "=" * 70)
    
    if len(expanded_results) > len(basic_results) or len(expanded_sources) > len(basic_sources):
        console.print("\n[bold green]✨ Query expansion improved retrieval:[/bold green]")
        console.print(f"   - Found {len(expanded_results) - len(basic_results)} more chunks")
        console.print(f"   - Covered {len(expanded_sources) - len(basic_sources)} more sources")
        console.print(f"   - Found {len(expanded_only)} unique chunks not found by basic retrieval")
    else:
        console.print("\n[yellow]⚠ Query expansion results similar to basic retrieval[/yellow]")
        console.print("   This may indicate:")
        console.print("   - Repository has limited relevant content")
        console.print("   - Basic query was already comprehensive")
        console.print("   - Collection needs more diverse documents")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

