"""
BRD Agent - Repository Analyzer
Automatically discover documentation and code structure in GitHub repositories.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from .github_client import GitHubClient

logger = logging.getLogger(__name__)


# Common documentation directory names
DOCUMENTATION_DIRS = {
    'docs', 'documentation', 'doc', 'wiki', 'guides', 'manual',
    'docs/', 'documentation/', 'doc/', 'wiki/', 'guides/', 'manual/'
}

# Common README file names
README_FILES = {
    'readme.md', 'readme.rst', 'readme.txt', 'readme',
    'README.md', 'README.rst', 'README.txt', 'README',
    'readme.markdown', 'README.markdown'
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    'django': {
        'files': ['manage.py', 'settings.py', 'wsgi.py', 'asgi.py'],
        'dirs': ['apps/', 'app/', 'src/'],
        'description': 'Django web framework'
    },
    'react': {
        'files': ['package.json'],
        'dirs': ['src/', 'components/', 'pages/', 'app/'],
        'description': 'React/Next.js frontend framework'
    },
    'python_package': {
        'files': ['setup.py', 'pyproject.toml', 'setup.cfg'],
        'dirs': ['src/', 'lib/', 'package/'],
        'description': 'Python package/library'
    },
    'nodejs': {
        'files': ['package.json', 'package-lock.json'],
        'dirs': ['src/', 'lib/', 'server/'],
        'description': 'Node.js application'
    },
    'generic': {
        'files': [],
        'dirs': ['src/', 'lib/', 'app/', 'server/'],
        'description': 'Generic code structure'
    }
}


def find_documentation_paths(repo_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find documentation directories in repository tree.
    
    Args:
        repo_tree: List of file/directory entries from GitHub API
        
    Returns:
        List of documentation path dictionaries with:
        - 'path': Directory path
        - 'priority': 'high'
        - 'file_count': Number of files in directory (if available)
        - 'description': Description of the directory
    """
    doc_paths = []
    found_paths: Set[str] = set()
    
    for item in repo_tree:
        item_path = item.get('path', '').lower()
        item_type = item.get('type', '')
        
        # Check if it's a documentation directory
        for doc_dir in DOCUMENTATION_DIRS:
            # Check exact match or starts with
            if item_path == doc_dir or item_path.startswith(doc_dir + '/'):
                if item_type in ('dir', 'tree') and item_path not in found_paths:
                    found_paths.add(item_path)
                    # Count markdown files in this directory
                    file_count = sum(
                        1 for i in repo_tree
                        if i.get('path', '').lower().startswith(item_path + '/')
                        and i.get('type') in ('file', 'blob')
                        and any(i.get('path', '').lower().endswith(ext) for ext in ['.md', '.rst', '.txt', '.markdown'])
                    )
                    
                    doc_paths.append({
                        'path': item.get('path', ''),  # Original case
                        'priority': 'high',
                        'file_count': file_count,
                        'description': f'Documentation directory: {item.get("path", "")}'
                    })
                    break
    
    # Sort by path length (shorter = more general, prefer those)
    doc_paths.sort(key=lambda x: (len(x['path']), x['path']))
    
    return doc_paths


def find_readme_files(repo_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find README files in repository tree.
    
    Args:
        repo_tree: List of file/directory entries from GitHub API
        
    Returns:
        List of README file dictionaries with:
        - 'path': File path
        - 'priority': 'high'
        - 'description': Description of the file
    """
    readme_files = []
    
    for item in repo_tree:
        item_path = item.get('path', '')
        item_type = item.get('type', '')
        
        # Check if it's a README file (case-insensitive)
        if item_type == 'file' or item_type == 'blob':
            path_lower = item_path.lower()
            # Check if filename matches README pattern
            filename = Path(item_path).name.lower()
            # Check exact match or starts with 'readme'
            if filename in README_FILES or filename.startswith('readme'):
                readme_files.append({
                    'path': item_path,
                    'priority': 'high',
                    'description': f'README file: {item_path}'
                })
    
    return readme_files


def detect_code_structure(repo_tree: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect code structure and framework patterns.
    
    Args:
        repo_tree: List of file/directory entries from GitHub API
        
    Returns:
        Dictionary with:
        - 'detected_framework': Framework name or 'generic'
        - 'main_code_paths': List of main code directory paths
        - 'framework_description': Description of detected framework
    """
    # Build sets of files and directories for quick lookup
    files = {item.get('path', '').lower() for item in repo_tree if item.get('type') == 'file'}
    dirs = {item.get('path', '').lower().rstrip('/') for item in repo_tree if item.get('type') in ('dir', 'tree')}
    
    # Detect framework
    detected_framework = 'generic'
    framework_description = 'Generic code structure'
    
    for framework, pattern in FRAMEWORK_PATTERNS.items():
        if framework == 'generic':
            continue
        
        # Check for framework-specific files
        file_matches = sum(1 for f in pattern['files'] if f.lower() in files)
        dir_matches = sum(1 for d in pattern['dirs'] if d.lower() in dirs or any(d.lower() in d2 for d2 in dirs))
        
        # If we find framework indicators, mark it
        if file_matches > 0 or dir_matches > 0:
            detected_framework = framework
            framework_description = pattern['description']
            break
    
    # Find main code paths
    main_code_paths = []
    code_dir_patterns = ['src/', 'lib/', 'app/', 'server/', 'backend/', 'frontend/']
    
    for item in repo_tree:
        item_path = item.get('path', '').lower()
        item_type = item.get('type', '')
        
        if item_type in ('dir', 'tree'):
            # Check if it matches code directory patterns
            for pattern in code_dir_patterns:
                if item_path == pattern or item_path.startswith(pattern):
                    # Count Python/JS/TS files in this directory
                    file_count = sum(
                        1 for i in repo_tree
                        if i.get('path', '').lower().startswith(item_path + '/')
                        and i.get('type') == 'file'
                        and any(i.get('path', '').lower().endswith(ext) 
                               for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs'])
                    )
                    
                    if file_count > 0:  # Only include if it has code files
                        main_code_paths.append({
                            'path': item.get('path', ''),  # Original case
                            'priority': 'medium',
                            'file_count': file_count,
                            'description': f'Code directory: {item.get("path", "")}'
                        })
                    break
    
    # Remove duplicates and sort
    seen = set()
    unique_paths = []
    for path_info in main_code_paths:
        if path_info['path'] not in seen:
            seen.add(path_info['path'])
            unique_paths.append(path_info)
    
    unique_paths.sort(key=lambda x: x['file_count'], reverse=True)  # Sort by file count
    
    return {
        'detected_framework': detected_framework,
        'framework_description': framework_description,
        'main_code_paths': unique_paths[:5],  # Top 5 code paths
    }


def generate_ingestion_plan(
    doc_paths: List[Dict[str, Any]],
    readme_files: List[Dict[str, Any]],
    code_structure: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate ingestion plan with prioritized paths.
    
    Args:
        doc_paths: List of documentation paths
        readme_files: List of README files
        code_structure: Code structure detection results
        
    Returns:
        List of ingestion plan items with:
        - 'path': Path to ingest
        - 'priority': 'high', 'medium', or 'low'
        - 'reason': Why this path should be ingested
    """
    plan = []
    
    # High priority: Documentation directories
    for doc_path in doc_paths:
        plan.append({
            'path': doc_path['path'],
            'priority': 'high',
            'reason': f"Documentation directory with {doc_path.get('file_count', 0)} files"
        })
    
    # High priority: README files
    for readme in readme_files:
        plan.append({
            'path': readme['path'],
            'priority': 'high',
            'reason': 'Main README file'
        })
    
    # Medium priority: Main code paths (if they have documentation potential)
    # Only include code paths that might have docstrings/comments
    for code_path in code_structure.get('main_code_paths', [])[:3]:  # Top 3 only
        plan.append({
            'path': code_path['path'],
            'priority': 'medium',
            'reason': f"Main code directory ({code_structure.get('detected_framework', 'generic')} framework)"
        })
    
    # Sort by priority (high first) and then by path
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    plan.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['path']))
    
    return plan


def analyze_repo(
    owner: str,
    repo: str,
    github_client: Optional[GitHubClient] = None
) -> Dict[str, Any]:
    """
    Analyze repository structure and generate ingestion plan.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        github_client: Optional GitHubClient instance (creates new if None)
        
    Returns:
        Dictionary with:
        - 'repository': Repository identifier
        - 'documentation_paths': List of documentation directories found
        - 'readme_files': List of README files found
        - 'code_structure': Code structure detection results
        - 'ingestion_plan': Prioritized ingestion plan
    """
    if github_client is None:
        github_client = GitHubClient()
    
    repo_url = f"https://github.com/{owner}/{repo}"
    logger.info(f"Analyzing repository: {repo_url}")
    
    try:
        # Get repository tree
        repo_tree = github_client.get_repo_tree(repo_url)
        logger.info(f"Fetched repository tree: {len(repo_tree)} items")
        
        # Find documentation paths
        doc_paths = find_documentation_paths(repo_tree)
        logger.info(f"Found {len(doc_paths)} documentation directories")
        
        # Find README files
        readme_files = find_readme_files(repo_tree)
        logger.info(f"Found {len(readme_files)} README files")
        
        # Detect code structure
        code_structure = detect_code_structure(repo_tree)
        logger.info(f"Detected framework: {code_structure.get('detected_framework', 'generic')}")
        
        # Generate ingestion plan
        ingestion_plan = generate_ingestion_plan(doc_paths, readme_files, code_structure)
        logger.info(f"Generated ingestion plan with {len(ingestion_plan)} items")
        
        return {
            'repository': f"{owner}/{repo}",
            'repository_url': repo_url,
            'documentation_paths': doc_paths,
            'readme_files': readme_files,
            'code_structure': code_structure,
            'ingestion_plan': ingestion_plan,
            'summary': {
                'total_items_analyzed': len(repo_tree),
                'documentation_dirs_found': len(doc_paths),
                'readme_files_found': len(readme_files),
                'ingestion_items': len(ingestion_plan),
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze repository {repo_url}: {e}", exc_info=True)
        raise

