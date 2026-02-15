#!/usr/bin/env python3
"""
BRD Agent - CLI Ingestion Tool
Bulk ingestion of GitHub repositories into ChromaDB vector store.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import time

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich import print as rprint

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.github_client import GitHubClient
from src.brd_agent.services.document_loaders import load_markdown
from src.brd_agent.services.chunking import chunk_markdown
from src.brd_agent.services.embeddings import EmbeddingService
from src.brd_agent.services.vector_store import VectorStore
from src.brd_agent.config import get_settings

app = typer.Typer(
    name="ingest",
    help="Ingest documentation from GitHub repositories into the vector store",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def find_markdown_files(repo_tree: List[Dict[str, Any]], path: str = "") -> List[str]:
    """
    Find all markdown files in repository tree.
    
    Args:
        repo_tree: List of file/directory items from GitHub API
        path: Optional path prefix to filter (if provided, only files under this path)
    
    Returns:
        List of file paths (relative to repo root)
    """
    markdown_files = []
    markdown_extensions = {'.md', '.rst', '.markdown'}
    
    # Normalize path prefix
    path_prefix = path.rstrip('/') + '/' if path else ''
    
    for item in repo_tree:
        item_path = item.get('path', '')
        item_type = item.get('type', '')
        
        # Skip if path prefix doesn't match
        if path_prefix and not item_path.startswith(path_prefix):
            continue
        
        # Check if it's a file with markdown extension
        if item_type == 'file' or item_type == 'blob':
            if any(item_path.lower().endswith(ext) for ext in markdown_extensions):
                markdown_files.append(item_path)
        # Note: For directories, GitHub recursive tree already includes all files
    
    return sorted(markdown_files)


def process_file(
    github_client: GitHubClient,
    repo_url: str,
    file_path: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
) -> Dict[str, Any]:
    """
    Process a single markdown file through the ingestion pipeline.
    
    Returns:
        Dictionary with processing results:
        - success: bool
        - file_path: str
        - chunks_count: int
        - error: Optional[str]
    """
    try:
        # Fetch file content
        content = github_client.get_file_content(repo_url, file_path)
        
        # Load markdown document
        doc = load_markdown(content, file_path)
        
        # Chunk document
        chunks = chunk_markdown(doc.content, doc.source_path)
        
        if not chunks:
            return {
                "success": True,
                "file_path": file_path,
                "chunks_count": 0,
                "error": None,
            }
        
        # Generate embeddings
        chunk_texts = [chunk['content'] for chunk in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)
        
        # Prepare metadata
        timestamp = datetime.utcnow().isoformat()
        metadatas: List[Dict[str, Any]] = []
        
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
        
        # Store in vector store
        vector_store.add_documents(
            repo_url=repo_url,
            documents=chunk_texts,
            embeddings=embeddings,
            metadata=metadatas,
        )
        
        return {
            "success": True,
            "file_path": file_path,
            "chunks_count": len(chunks),
            "error": None,
        }
        
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "chunks_count": 0,
            "error": str(e),
        }


@app.command(name="github")
def github(
    repo_url: Optional[str] = typer.Argument(
        None,
        help="GitHub repository URL (e.g., https://github.com/owner/repo). If not provided, uses default from config."
    ),
    path: Optional[str] = typer.Option(
        None,
        "--path",
        "-p",
        help="Specific path within repository to ingest (e.g., 'docs/'). If not provided, ingests entire repository."
    ),
):
    """
    Ingest markdown documentation from a GitHub repository.
    
    Examples:
        # Use default repo from config
        python -m cli.ingest github
        
        # Ingest specific repository
        python -m cli.ingest github https://github.com/paperless-ngx/paperless-ngx
        
        # Ingest specific path
        python -m cli.ingest github https://github.com/owner/repo --path docs/
    """
    settings = get_settings()
    
    # Use provided repo_url or default from config
    if repo_url is None:
        repo_url = settings.default_repo_url
        rprint(f"[dim]Using default repository from config: {repo_url}[/dim]")
    else:
        rprint(f"[dim]Using repository: {repo_url}[/dim]")
    
    rprint(f"\n[bold blue]🚀 Starting ingestion for: {repo_url}[/bold blue]")
    
    start_time = time.time()
    
    # Initialize services
    try:
        github_client = GitHubClient()
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
    except Exception as e:
        console.print(f"[bold red]✗ Failed to initialize services: {e}[/bold red]")
        raise typer.Exit(1)
    
    # Fetch repository tree
    rprint("\n[bold]📂 Fetching repository structure...[/bold]")
    try:
        repo_tree = github_client.get_repo_tree(repo_url, path or "")
        rprint(f"[green]✓[/green] Found {len(repo_tree)} items in repository")
    except Exception as e:
        console.print(f"[bold red]✗ Failed to fetch repository tree: {e}[/bold red]")
        raise typer.Exit(1)
    
    # Find markdown files
    rprint("\n[bold]🔍 Finding markdown files...[/bold]")
    markdown_files = find_markdown_files(repo_tree, path or "")
    
    if not markdown_files:
        console.print("[yellow]⚠ No markdown files found in repository[/yellow]")
        raise typer.Exit(0)
    
    rprint(f"[green]✓[/green] Found {len(markdown_files)} markdown file(s)")
    
    # Process files
    rprint(f"\n[bold]📝 Processing {len(markdown_files)} file(s)...[/bold]\n")
    
    results: List[Dict[str, Any]] = []
    total_chunks = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=len(markdown_files))
        
        for file_path in markdown_files:
            progress.update(task, description=f"Processing: {file_path[:50]}...")
            
            result = process_file(
                github_client=github_client,
                repo_url=repo_url,
                file_path=file_path,
                embedding_service=embedding_service,
                vector_store=vector_store,
            )
            
            results.append(result)
            if result["success"]:
                total_chunks += result["chunks_count"]
            
            progress.advance(task)
    
    # Calculate statistics
    elapsed_time = time.time() - start_time
    successful_files = sum(1 for r in results if r["success"])
    failed_files = len(results) - successful_files
    
    # Display summary
    rprint("\n" + "=" * 70)
    rprint("[bold green]✅ Ingestion Complete![/bold green]")
    rprint("=" * 70)
    
    # Summary table
    table = Table(title="Ingestion Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Repository", repo_url)
    table.add_row("Files Found", str(len(markdown_files)))
    table.add_row("Files Processed", f"{successful_files}/{len(markdown_files)}")
    table.add_row("Files Failed", str(failed_files))
    table.add_row("Total Chunks Created", str(total_chunks))
    table.add_row("Collection Name", vector_store.get_collection_name(repo_url))
    table.add_row("Time Taken", f"{elapsed_time:.2f} seconds")
    
    console.print(table)
    
    # Show failed files if any
    if failed_files > 0:
        rprint("\n[bold yellow]⚠ Failed Files:[/bold yellow]")
        for result in results:
            if not result["success"]:
                rprint(f"  • {result['file_path']}: {result['error']}")
    
    # Verify collection
    collection = vector_store.get_collection(repo_url)
    if collection:
        doc_count = collection.count()
        rprint(f"\n[dim]Collection '{vector_store.get_collection_name(repo_url)}' now contains {doc_count} document(s)[/dim]")
    
    rprint("\n[bold green]✨ Done![/bold green]\n")


if __name__ == "__main__":
    app()

