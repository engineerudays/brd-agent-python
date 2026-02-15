#!/usr/bin/env python3
"""
Test script for Step 13: API Endpoints for Ingestion

Tests all ingestion API endpoints:
1. POST /api/ingest/document - Ingest single document
2. POST /api/ingest/repo-path - Ingest repository path
3. GET /api/ingest/status - Check ingestion status
4. GET /api/ingest/repos - List all repositories
5. DELETE /api/ingest/document - Remove document
6. DELETE /api/ingest/repo - Remove repository collection
"""

import sys
import json
import requests
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

# API base URL
API_BASE_URL = "http://localhost:8000"


def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return response."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        elif method == "DELETE":
            response = requests.delete(url, params=params, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json(),
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Connection refused - Is the API server running? (uvicorn api.main:app)",
        }
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
        except:
            error_data = {"detail": str(e)}
        return {
            "success": False,
            "status_code": e.response.status_code,
            "error": error_data,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def main():
    """Run all API endpoint tests."""
    console.print("\n[bold blue]" + "=" * 70)
    console.print("[bold blue]Step 13: API Endpoints for Ingestion - Test[/bold blue]")
    console.print("[bold blue]" + "=" * 70)
    
    # Test repository URL
    test_repo_url = "https://github.com/paperless-ngx/paperless-ngx"
    test_file_path = "README.md"
    test_path = "docs/"
    
    results = []
    
    # Test 1: List repos (before ingestion)
    console.print("\n[bold yellow]Test 1: List Repositories (before ingestion)[/bold yellow]")
    result = test_endpoint("GET", "/api/ingest/repos")
    results.append(("GET /api/ingest/repos", result))
    if result["success"]:
        console.print(f"[green]✓[/green] Found {result['data'].get('total', 0)} repositories")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 2: Check status (before ingestion)
    console.print("\n[bold yellow]Test 2: Check Ingestion Status (before ingestion)[/bold yellow]")
    result = test_endpoint("GET", "/api/ingest/status", params={"repo_url": test_repo_url})
    results.append(("GET /api/ingest/status", result))
    if result["success"]:
        status_data = result["data"]
        console.print(f"[green]✓[/green] Repository exists: {status_data.get('exists', False)}")
        console.print(f"   Document count: {status_data.get('document_count', 0)}")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 3: Ingest single document
    console.print("\n[bold yellow]Test 3: Ingest Single Document[/bold yellow]")
    console.print(f"   Repository: {test_repo_url}")
    console.print(f"   File: {test_file_path}")
    result = test_endpoint("POST", "/api/ingest/document", data={
        "repo_url": test_repo_url,
        "file_path": test_file_path,
    })
    results.append(("POST /api/ingest/document", result))
    if result["success"]:
        ingest_data = result["data"]
        console.print(f"[green]✓[/green] {ingest_data.get('message', 'Success')}")
        console.print(f"   Files processed: {ingest_data.get('files_processed', 0)}")
        console.print(f"   Chunks created: {ingest_data.get('chunks_created', 0)}")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 4: Check status (after single document ingestion)
    console.print("\n[bold yellow]Test 4: Check Ingestion Status (after single document)[/bold yellow]")
    result = test_endpoint("GET", "/api/ingest/status", params={"repo_url": test_repo_url})
    results.append(("GET /api/ingest/status (after)", result))
    if result["success"]:
        status_data = result["data"]
        console.print(f"[green]✓[/green] Repository exists: {status_data.get('exists', True)}")
        console.print(f"   Document count: {status_data.get('document_count', 0)}")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 5: Ingest repository path
    console.print("\n[bold yellow]Test 5: Ingest Repository Path[/bold yellow]")
    console.print(f"   Repository: {test_repo_url}")
    console.print(f"   Path: {test_path}")
    console.print("[dim]   (This may take a while...)[/dim]")
    result = test_endpoint("POST", "/api/ingest/repo-path", data={
        "repo_url": test_repo_url,
        "path": test_path,
    })
    results.append(("POST /api/ingest/repo-path", result))
    if result["success"]:
        ingest_data = result["data"]
        console.print(f"[green]✓[/green] {ingest_data.get('message', 'Success')}")
        console.print(f"   Files processed: {ingest_data.get('files_processed', 0)}")
        console.print(f"   Chunks created: {ingest_data.get('chunks_created', 0)}")
        if ingest_data.get('errors'):
            console.print(f"[yellow]⚠[/yellow] {len(ingest_data['errors'])} errors occurred")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 6: List repos (after ingestion)
    console.print("\n[bold yellow]Test 6: List Repositories (after ingestion)[/bold yellow]")
    result = test_endpoint("GET", "/api/ingest/repos")
    results.append(("GET /api/ingest/repos (after)", result))
    if result["success"]:
        repos_data = result["data"]
        console.print(f"[green]✓[/green] Found {repos_data.get('total', 0)} repositories")
        for repo in repos_data.get('repos', [])[:5]:
            console.print(f"   • {repo.get('repo_url', 'unknown')}: {repo.get('document_count', 0)} documents")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 7: Delete document
    console.print("\n[bold yellow]Test 7: Delete Document[/bold yellow]")
    console.print(f"   Repository: {test_repo_url}")
    console.print(f"   File: {test_file_path}")
    result = test_endpoint("DELETE", "/api/ingest/document", params={
        "repo_url": test_repo_url,
        "file_path": test_file_path,
    })
    results.append(("DELETE /api/ingest/document", result))
    if result["success"]:
        delete_data = result["data"]
        console.print(f"[green]✓[/green] {delete_data.get('message', 'Success')}")
        console.print(f"   Chunks deleted: {delete_data.get('chunks_deleted', 0)}")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Test 8: Delete repository collection
    console.print("\n[bold yellow]Test 8: Delete Repository Collection[/bold yellow]")
    console.print(f"   Repository: {test_repo_url}")
    result = test_endpoint("DELETE", "/api/ingest/repo", params={
        "repo_url": test_repo_url,
    })
    results.append(("DELETE /api/ingest/repo", result))
    if result["success"]:
        delete_data = result["data"]
        console.print(f"[green]✓[/green] {delete_data.get('message', 'Success')}")
    else:
        console.print(f"[red]✗[/red] {result.get('error', 'Unknown error')}")
    
    # Summary
    console.print("\n[bold magenta]" + "=" * 70)
    console.print("[bold magenta]Test Summary[/bold magenta]")
    console.print("[bold magenta]" + "=" * 70)
    
    table = Table(title="API Endpoint Test Results", show_header=True, header_style="bold cyan")
    table.add_column("Endpoint", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    for endpoint, result in results:
        if result["success"]:
            status = "✓ Success"
            details = f"Status: {result.get('status_code', 'N/A')}"
        else:
            status = "✗ Failed"
            error = result.get('error', {})
            if isinstance(error, dict):
                details = error.get('detail', str(error))
            else:
                details = str(error)
        
        table.add_row(endpoint, status, details[:60])
    
    console.print(table)
    
    # Final status
    successful = sum(1 for _, r in results if r["success"])
    total = len(results)
    
    console.print(f"\n[bold]Results:[/bold] {successful}/{total} tests passed")
    
    if successful == total:
        console.print("\n[bold green]✅ All API endpoint tests passed![/bold green]")
        return 0
    else:
        console.print("\n[bold yellow]⚠ Some tests failed - check API server is running[/bold yellow]")
        console.print("[dim]Start API server with: uvicorn api.main:app --reload[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())

