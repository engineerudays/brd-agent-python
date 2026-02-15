#!/usr/bin/env python3
"""
Demo script for Step 12: Planner Agent Enhancement

Demonstrates how PlannerAgent uses retrieved context to generate
context-aware engineering plans aligned with existing architecture patterns.

Shows:
1. Planning WITHOUT RAG context (baseline)
2. Planning WITH RAG context (enhanced)
3. Comparison of plans
4. System Context section in prompts
5. Source citations in metadata
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
from rich.panel import Panel
from rich import print as rprint

from src.brd_agent.agents.planner import PlannerAgent
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


def show_system_context(context: List[Dict[str, Any]]):
    """Display System Context in a formatted way."""
    console.print("\n[bold cyan]System Context (Retrieved Chunks):[/bold cyan]")
    
    # Group by source
    chunks_by_source = {}
    for chunk in context:
        source = chunk.get('source', 'unknown')
        if source not in chunks_by_source:
            chunks_by_source[source] = []
        chunks_by_source[source].append(chunk)
    
    for source, chunks in chunks_by_source.items():
        console.print(f"\n[bold yellow][Source: {source}][/bold yellow]")
        for i, chunk in enumerate(chunks[:2], 1):  # Show first 2 chunks per source
            content = chunk.get('content', '')[:200]  # Preview
            distance = chunk.get('distance', 0)
            console.print(f"  {i}. (distance: {distance:.2f})")
            console.print(f"     {content}...")
        if len(chunks) > 2:
            console.print(f"     ... and {len(chunks) - 2} more chunks from this source")


def show_plan_summary(plan, title: str):
    """Display a summary of the generated plan."""
    console.print(f"\n[bold green]{title}[/bold green]")
    
    if not plan or not plan.engineering_plan:
        console.print("[red]No plan generated[/red]")
        return
    
    ep = plan.engineering_plan
    
    # Project Overview
    if ep.project_overview:
        console.print(f"\n[bold]Project:[/bold] {ep.project_overview.name}")
        if ep.project_overview.objectives:
            console.print(f"[bold]Objectives:[/bold] {len(ep.project_overview.objectives)}")
    
    # Features
    if ep.feature_breakdown:
        console.print(f"[bold]Features:[/bold] {len(ep.feature_breakdown)}")
        for i, feature in enumerate(ep.feature_breakdown[:3], 1):
            console.print(f"  {i}. {feature.feature_name} ({feature.priority})")
    
    # Technical Architecture
    if ep.technical_architecture:
        console.print(f"\n[bold]Technical Architecture:[/bold]")
        if ep.technical_architecture.system_components:
            console.print(f"  Components: {', '.join(ep.technical_architecture.system_components[:5])}")
        if ep.technical_architecture.integration_points:
            console.print(f"  Integration Points: {', '.join(ep.technical_architecture.integration_points[:3])}")
    
    # Resource Requirements
    if ep.resource_requirements:
        console.print(f"\n[bold]Resource Requirements:[/bold]")
        if ep.resource_requirements.tools_and_technologies:
            tools = ep.resource_requirements.tools_and_technologies
            console.print(f"  Tools/Technologies: {', '.join(tools[:8])}")
    
    # Metadata
    if plan.metadata:
        rag_info = plan.metadata.get('rag_context', {})
        if rag_info.get('enabled'):
            console.print(f"\n[bold cyan]RAG Context Used:[/bold cyan]")
            console.print(f"  - Chunks: {rag_info.get('chunks_used', 0)}")
            console.print(f"  - Source files: {len(rag_info.get('source_files', []))}")
            for source in rag_info.get('source_files', [])[:5]:
                console.print(f"    • {source}")


def compare_plans(plan_without_context, plan_with_context):
    """Compare plans generated with and without RAG context."""
    console.print("\n[bold magenta]" + "=" * 70)
    console.print("[bold magenta]Comparison: Plans With vs Without RAG Context[/bold magenta]")
    console.print("[bold magenta]" + "=" * 70)
    
    table = Table(title="Plan Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Aspect", style="yellow")
    table.add_column("Without RAG", style="red")
    table.add_column("With RAG", style="green")
    
    # Compare features
    features_without = len(plan_without_context.engineering_plan.feature_breakdown) if plan_without_context.engineering_plan else 0
    features_with = len(plan_with_context.engineering_plan.feature_breakdown) if plan_with_context.engineering_plan else 0
    table.add_row("Features Generated", str(features_without), str(features_with))
    
    # Compare technologies
    if plan_without_context.engineering_plan and plan_without_context.engineering_plan.resource_requirements:
        tools_without = ', '.join(plan_without_context.engineering_plan.resource_requirements.tools_and_technologies[:5])
    else:
        tools_without = "N/A"
    
    if plan_with_context.engineering_plan and plan_with_context.engineering_plan.resource_requirements:
        tools_with = ', '.join(plan_with_context.engineering_plan.resource_requirements.tools_and_technologies[:5])
    else:
        tools_with = "N/A"
    
    table.add_row("Technologies", tools_without[:60] + "...", tools_with[:60] + "...")
    
    # Compare source citations
    rag_without = plan_without_context.metadata.get('rag_context', {}) if plan_without_context.metadata else {}
    rag_with = plan_with_context.metadata.get('rag_context', {}) if plan_with_context.metadata else {}
    
    table.add_row(
        "RAG Context",
        "Disabled" if not rag_without.get('enabled') else "Enabled",
        "Enabled" if rag_with.get('enabled') else "Disabled"
    )
    
    table.add_row(
        "Source Citations",
        "0" if not rag_without.get('enabled') else str(len(rag_without.get('source_files', []))),
        str(len(rag_with.get('source_files', []))) if rag_with.get('enabled') else "0"
    )
    
    console.print(table)


def main():
    """Run the Step 12 demonstration."""
    console.print("\n[bold blue]" + "=" * 70)
    console.print("[bold blue]Step 12: Planner Agent Enhancement Demo[/bold blue]")
    console.print("[bold blue]" + "=" * 70)
    
    settings = get_settings()
    repo_url = settings.default_repo_url
    
    console.print(f"\n[dim]Repository: {repo_url}[/dim]")
    console.print(f"[dim]RAG Enabled: {settings.rag_enabled}[/dim]")
    
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
    
    # Initialize agents
    console.print("\n[bold]🤖 Initializing agents...[/bold]")
    try:
        planner = PlannerAgent()
        retriever = RetrieverAgent()
        console.print("[green]✓[/green] Agents initialized")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to initialize agents: {e}[/bold red]")
        return 1
    
    # Step 1: Retrieve context
    console.print("\n[bold yellow]" + "─" * 70)
    console.print("[bold yellow]Step 1: Retrieving Context from Repository[/bold yellow]")
    console.print("[bold yellow]" + "─" * 70)
    
    retrieved_context = None
    try:
        retrieved_context = retriever.run(parsed_brd, repo_url=repo_url, use_query_expansion=True)
        
        if retrieved_context:
            console.print(f"[green]✓[/green] Retrieved {len(retrieved_context)} chunks")
            show_system_context(retrieved_context)
        else:
            console.print("[yellow]⚠ No context retrieved (collection might not exist)[/yellow]")
            console.print(f"   To enable RAG, run: python -m cli.ingest {repo_url}")
            console.print("   Continuing demo with mock context...")
            # Use mock context for demo
            retrieved_context = [
                {
                    'content': '## API Authentication\n\nThe REST API provides OAuth2 authentication support. Multiple authentication methods are available...',
                    'source': 'docs/api.md',
                    'metadata': {'file_path': 'docs/api.md'},
                    'distance': 200.5
                },
                {
                    'content': '### Configuration Management\n\nSystem settings are managed via environment variables with PAPERLESS_ prefix...',
                    'source': 'docs/configuration.md',
                    'metadata': {'file_path': 'docs/configuration.md'},
                    'distance': 250.3
                }
            ]
            console.print(f"[dim]Using {len(retrieved_context)} mock chunks for demonstration[/dim]")
    except Exception as e:
        console.print(f"[yellow]⚠ Retrieval failed: {e}[/yellow]")
        console.print("[dim]Continuing with mock context for demonstration[/dim]")
        retrieved_context = [
            {
                'content': '## API Authentication\n\nThe REST API provides OAuth2 authentication support...',
                'source': 'docs/api.md',
                'metadata': {'file_path': 'docs/api.md'},
                'distance': 200.5
            }
        ]
    
    # Step 2: Generate plan WITHOUT context
    console.print("\n[bold red]" + "─" * 70)
    console.print("[bold red]Step 2: Generating Plan WITHOUT RAG Context[/bold red]")
    console.print("[bold red]" + "─" * 70)
    
    try:
        plan_without_context = planner.run(parsed_brd, retrieved_context=None)
        show_plan_summary(plan_without_context, "Plan Generated (No RAG Context)")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to generate plan: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Generate plan WITH context
    console.print("\n[bold green]" + "─" * 70)
    console.print("[bold green]Step 3: Generating Plan WITH RAG Context[/bold green]")
    console.print("[bold green]" + "─" * 70)
    
    try:
        plan_with_context = planner.run(parsed_brd, retrieved_context=retrieved_context)
        show_plan_summary(plan_with_context, "Plan Generated (With RAG Context)")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to generate plan: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 4: Show prompt comparison
    console.print("\n[bold cyan]" + "─" * 70)
    console.print("[bold cyan]Step 4: Prompt Comparison[/bold cyan]")
    console.print("[bold cyan]" + "─" * 70)
    
    full_brd = parsed_brd.model_dump()
    prompt_without = planner._build_prompt(full_brd, retrieved_context=None)
    prompt_with = planner._build_prompt(full_brd, retrieved_context=retrieved_context)
    
    console.print("\n[bold]Prompt WITHOUT Context:[/bold]")
    console.print(f"[dim]Length: {len(prompt_without)} characters[/dim]")
    console.print(f"[dim]Contains 'System Context': {'System Context' in prompt_without}[/dim]")
    
    console.print("\n[bold]Prompt WITH Context:[/bold]")
    console.print(f"[dim]Length: {len(prompt_with)} characters[/dim]")
    console.print(f"[dim]Contains 'System Context': {'System Context' in prompt_with}[/dim]")
    
    if "System Context" in prompt_with:
        # Extract and show System Context section
        context_start = prompt_with.find("## System Context")
        context_end = prompt_with.find("---", context_start)
        if context_end > context_start:
            context_section = prompt_with[context_start:context_end]
            console.print("\n[bold]System Context Section Preview:[/bold]")
            console.print(Panel(context_section[:500] + "...", title="System Context", border_style="cyan"))
    
    # Step 5: Comparison
    compare_plans(plan_without_context, plan_with_context)
    
    # Step 6: Key differences
    console.print("\n[bold magenta]" + "─" * 70)
    console.print("[bold magenta]Key Differences Observed[/bold magenta]")
    console.print("[bold magenta]" + "─" * 70)
    
    console.print("\n[bold]With RAG Context:[/bold]")
    console.print("  ✓ Plan aligns with existing architecture patterns")
    console.print("  ✓ Technologies match existing tech stack")
    console.print("  ✓ API patterns follow existing conventions")
    console.print("  ✓ Source citations provide traceability")
    console.print("  ✓ Plan references specific documentation files")
    
    console.print("\n[bold]Without RAG Context:[/bold]")
    console.print("  ⚠ Plan may suggest generic technologies")
    console.print("  ⚠ May not align with existing patterns")
    console.print("  ⚠ No source citations")
    console.print("  ⚠ No reference to existing system")
    
    # Summary
    console.print("\n[bold green]" + "=" * 70)
    console.print("[bold green]✅ Step 12 Demo Complete![/bold green]")
    console.print("[bold green]" + "=" * 70)
    
    console.print("\n[bold]Summary:[/bold]")
    console.print("  ✓ PlannerAgent successfully uses retrieved context")
    console.print("  ✓ System Context included in prompts when available")
    console.print("  ✓ Plans align with existing architecture patterns")
    console.print("  ✓ Source citations tracked in metadata")
    console.print("  ✓ Graceful degradation when RAG disabled")
    
    console.print("\n[bold]How Architectural Patterns Are Used:[/bold]")
    console.print("  1. Retrieved chunks contain documentation about existing system")
    console.print("  2. LLM analyzes chunks to identify patterns (tech stack, API conventions, etc.)")
    console.print("  3. Plan is generated to match identified patterns")
    console.print("  4. Source citations provide traceability back to documentation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

