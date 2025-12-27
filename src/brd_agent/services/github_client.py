"""
BRD Agent - GitHub API Client
Client for fetching files and repository structure from GitHub.
"""

import re
import time
from typing import Optional, Tuple, Dict, Any, List, Union
import httpx
import logging
import base64

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub API client for fetching repository files and structure.
    
    Supports public repositories without authentication.
    Includes basic rate limit handling with retry logic.
    """
    
    def __init__(self, base_url: str = "https://api.github.com"):
        """
        Initialize GitHub API client.
        
        Args:
            base_url: GitHub API base URL (default: https://api.github.com)
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "BRD-Agent-Python/1.0",
            },
        )
        logger.info(f"GitHubClient initialized: {self.base_url}")
    
    def parse_repo_url(self, repo_url: Union[str, Tuple[str, str]]) -> Tuple[str, str]:
        """
        Parse GitHub repository URL to extract owner and repo name.
        
        Supports:
        - Full URL: "https://github.com/owner/repo"
        - Short URL: "github.com/owner/repo"
        - Tuple: ("owner", "repo")
        
        Args:
            repo_url: GitHub repository URL or (owner, repo) tuple
            
        Returns:
            Tuple of (owner, repo)
            
        Raises:
            ValueError: If URL format is invalid
        """
        # If already a tuple, return as-is
        if isinstance(repo_url, tuple):
            if len(repo_url) == 2:
                return repo_url
            else:
                raise ValueError(f"Invalid tuple format: {repo_url}")
        
        # Parse URL
        # Pattern: https://github.com/owner/repo or github.com/owner/repo
        pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/?#]+)'
        match = re.search(pattern, repo_url.lower())
        
        if not match:
            raise ValueError(f"Invalid GitHub URL format: {repo_url}")
        
        owner, repo = match.groups()
        
        # Remove .git suffix if present
        repo = repo.rstrip('.git')
        
        return (owner, repo)
    
    def get_repo_tree(
        self,
        repo_url: Union[str, Tuple[str, str]],
        path: str = "",
        ref: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        Get directory tree structure from GitHub repository.
        
        Args:
            repo_url: GitHub repository URL or (owner, repo) tuple
            path: Path within repository (default: root "")
            ref: Git reference (branch, tag, or SHA) (default: "main")
            
        Returns:
            List of file/directory entries with:
            - 'path': File/directory path
            - 'type': 'file' or 'dir'
            - 'size': File size (for files)
            - 'sha': Git SHA
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If repo_url is invalid
        """
        owner, repo = self.parse_repo_url(repo_url)
        
        # Get default branch if ref is "main" (GitHub might use "master")
        if ref == "main":
            try:
                repo_info = self._make_request(f"/repos/{owner}/{repo}")
                ref = repo_info.get("default_branch", "main")
            except Exception:
                # Fallback to main if we can't get default branch
                pass
        
        # Get tree SHA for the path
        if path:
            # Get contents of specific path
            contents = self._make_request(f"/repos/{owner}/{repo}/contents/{path}", params={"ref": ref})
            
            if isinstance(contents, dict):
                # Single file
                return [contents]
            elif isinstance(contents, list):
                # Directory
                return contents
            else:
                return []
        else:
            # Get root tree
            # First get the commit SHA
            commits = self._make_request(f"/repos/{owner}/{repo}/commits/{ref}")
            commit_sha = commits["sha"]
            
            # Get tree SHA from commit
            commit = self._make_request(f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
            tree_sha = commit["tree"]["sha"]
            
            # Get tree contents
            tree = self._make_request(f"/repos/{owner}/{repo}/git/trees/{tree_sha}", params={"recursive": "1"})
            return tree.get("tree", [])
    
    def get_file_content(
        self,
        repo_url: Union[str, Tuple[str, str]],
        path: str,
        ref: str = "main"
    ) -> str:
        """
        Fetch file content from GitHub repository.
        
        Args:
            repo_url: GitHub repository URL or (owner, repo) tuple
            path: File path within repository (e.g., "README.md")
            ref: Git reference (branch, tag, or SHA) (default: "main")
            
        Returns:
            File content as string (decoded from base64)
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If repo_url is invalid or file not found
        """
        owner, repo = self.parse_repo_url(repo_url)
        
        # Get file content
        file_info = self._make_request(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref}
        )
        
        # Check if it's a file
        if file_info.get("type") != "file":
            raise ValueError(f"Path {path} is not a file (type: {file_info.get('type')})")
        
        # Decode base64 content
        content_encoded = file_info.get("content", "")
        if not content_encoded:
            raise ValueError(f"File {path} has no content")
        
        # GitHub API returns base64-encoded content with newlines
        content_encoded = content_encoded.replace("\n", "")
        try:
            content = base64.b64decode(content_encoded).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to decode file content: {e}")
        
        return content
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make HTTP request to GitHub API with rate limit handling.
        
        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo")
            params: Query parameters
            max_retries: Maximum number of retries for rate limits
            
        Returns:
            JSON response (dict or list)
            
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        for attempt in range(max_retries):
            try:
                response = self.client.get(endpoint, params=params)
                
                # Check rate limit
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if rate_limit_remaining == "0":
                        # Rate limited - wait and retry
                        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                        wait_time = max(1, reset_time - int(time.time()))
                        
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                            continue
                        else:
                            response.raise_for_status()
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"Resource not found: {endpoint}")
                elif e.response.status_code == 403 and attempt < max_retries - 1:
                    # Rate limit - already handled above, but catch here too
                    continue
                else:
                    raise
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
        
        raise httpx.HTTPError("Max retries exceeded")
    
    def __del__(self):
        """Cleanup httpx client on deletion"""
        if hasattr(self, 'client'):
            try:
                self.client.close()
            except Exception:
                pass

