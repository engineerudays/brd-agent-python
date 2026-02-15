#!/usr/bin/env python3
"""
Test script for Step 15: Repository Analyzer

Tests repository analysis functionality:
1. Analyze paperless-ngx repository
2. Verify documentation paths are found
3. Verify README files are found
4. Verify code structure is detected
5. Verify ingestion plan is generated
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich import print as rprint

from src.brd_agent.services.repository_analyzer import analyze_repo
from src.brd_agent.services.github_client import GitHubClient

console = Console()


def test_analyze_paperless_ngx():
    """Test analyzing paperless-ngx repository."""
    print("\n" + "=" * 70)
    print("Step 15: Repository Analyzer - Test")
    print("=" * 70)
    
    owner = "paperless-ngx"
    repo = "paperless-ngx"
    
    print(f"\n[bold]Analyzing repository: {owner}/{repo}[/bold]")
    print("[dim]This may take a moment...[/dim]\n")
    
    try:
        github_client = GitHubClient()
        result = analyze_repo(owner, repo, github_client)
        
        # Display summary
        print("\n[bold green]" + "=" * 70)
        print("[bold green]Analysis Results[/bold green]")
        print("[bold green]" + "=" * 70)
        
        summary = result.get('summary', {})
        print(f"\n[bold]Summary:[/bold]")
        print(f"  - Total items analyzed: {summary.get('total_items_analyzed', 0)}")
        print(f"  - Documentation directories: {summary.get('documentation_dirs_found', 0)}")
        print(f"  - README files: {summary.get('readme_files_found', 0)}")
        print(f"  - Ingestion plan items: {summary.get('ingestion_items', 0)}")
        
        # Documentation paths
        doc_paths = result.get('documentation_paths', [])
        if doc_paths:
            print(f"\n[bold green]Documentation Paths Found ({len(doc_paths)}):[/bold green]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Path", style="yellow")
            table.add_column("Priority", style="green")
            table.add_column("Files", style="white")
            table.add_column("Description", style="dim")
            
            for doc in doc_paths:
                table.add_row(
                    doc['path'],
                    doc['priority'],
                    str(doc.get('file_count', 0)),
                    doc.get('description', '')[:50]
                )
            console.print(table)
        else:
            print("\n[yellow]⚠ No documentation directories found[/yellow]")
        
        # README files
        readme_files = result.get('readme_files', [])
        if readme_files:
            print(f"\n[bold green]README Files Found ({len(readme_files)}):[/bold green]")
            for readme in readme_files:
                print(f"  • {readme['path']} ({readme['priority']} priority)")
        else:
            print("\n[yellow]⚠ No README files found[/yellow]")
        
        # Code structure
        code_structure = result.get('code_structure', {})
        print(f"\n[bold green]Code Structure:[/bold green]")
        print(f"  - Detected Framework: {code_structure.get('detected_framework', 'unknown')}")
        print(f"  - Description: {code_structure.get('framework_description', 'N/A')}")
        
        main_code_paths = code_structure.get('main_code_paths', [])
        if main_code_paths:
            print(f"\n  Main Code Paths ({len(main_code_paths)}):")
            for code_path in main_code_paths:
                print(f"    • {code_path['path']} ({code_path['priority']} priority, {code_path.get('file_count', 0)} files)")
        
        # Ingestion plan
        ingestion_plan = result.get('ingestion_plan', [])
        if ingestion_plan:
            print(f"\n[bold green]Ingestion Plan ({len(ingestion_plan)} items):[/bold green]")
            plan_table = Table(show_header=True, header_style="bold cyan")
            plan_table.add_column("Priority", style="green")
            plan_table.add_column("Path", style="yellow")
            plan_table.add_column("Reason", style="white")
            
            for item in ingestion_plan:
                priority_style = {
                    'high': '[bold red]high[/bold red]',
                    'medium': '[yellow]medium[/yellow]',
                    'low': '[dim]low[/dim]'
                }.get(item['priority'], item['priority'])
                
                plan_table.add_row(
                    item['priority'],
                    item['path'],
                    item.get('reason', '')[:60]
                )
            console.print(plan_table)
        else:
            print("\n[yellow]⚠ No ingestion plan generated[/yellow]")
        
        # Verification
        print("\n[bold]" + "=" * 70)
        print("[bold]Verification[/bold]")
        print("=" * 70)
        
        checks = []
        
        # Check 1: Documentation directory found
        if doc_paths:
            docs_found = any('docs' in d['path'].lower() for d in doc_paths)
            checks.append(("Documentation directory (docs/) found", docs_found))
            if docs_found:
                print("✓ Documentation directory found")
            else:
                print("⚠ Documentation directory not found (but other doc dirs may exist)")
        else:
            checks.append(("Documentation directory found", False))
            print("✗ No documentation directories found")
        
        # Check 2: README file found
        readme_found = len(readme_files) > 0
        checks.append(("README file found", readme_found))
        if readme_found:
            print("✓ README file found")
        else:
            print("✗ No README files found")
        
        # Check 3: Code structure detected
        framework_detected = code_structure.get('detected_framework') != 'generic'
        checks.append(("Code structure detected", framework_detected or len(main_code_paths) > 0))
        if framework_detected:
            print(f"✓ Framework detected: {code_structure.get('detected_framework')}")
        elif main_code_paths:
            print("✓ Code structure detected (generic)")
        else:
            print("⚠ Code structure not clearly detected")
        
        # Check 4: Ingestion plan generated
        plan_generated = len(ingestion_plan) > 0
        checks.append(("Ingestion plan generated", plan_generated))
        if plan_generated:
            print(f"✓ Ingestion plan generated with {len(ingestion_plan)} items")
        else:
            print("✗ No ingestion plan generated")
        
        # Overall result
        all_passed = all(check[1] for check in checks)
        
        print("\n" + "=" * 70)
        if all_passed:
            print("[bold green]✅ All checks passed![/bold green]")
        else:
            print("[bold yellow]⚠ Some checks failed (see details above)[/bold yellow]")
        print("=" * 70)
        
        # Save results to file for inspection
        output_file = project_root / ".cursor" / "build" / "step15_analysis_result.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[dim]Full results saved to: {output_file}[/dim]")
        
        return all_passed
        
    except Exception as e:
        print(f"\n[bold red]✗ Analysis failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests."""
    success = test_analyze_paperless_ngx()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

