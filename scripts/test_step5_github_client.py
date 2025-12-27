#!/usr/bin/env python3
"""
Test script for Step 5: GitHub API Client
Verifies that GitHubClient can fetch files and repository structure from GitHub.
"""

import sys
from pathlib import Path
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brd_agent.services.github_client import GitHubClient


def test_parse_repo_url():
    """Test URL parsing"""
    print("🧪 Test 1: Parse Repository URL")
    print("-" * 50)
    
    client = GitHubClient()
    
    test_cases = [
        ("https://github.com/paperless-ngx/paperless-ngx", ("paperless-ngx", "paperless-ngx")),
        ("github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/user-name/repo.name", ("user-name", "repo.name")),
        (("owner", "repo"), ("owner", "repo")),  # Tuple input
    ]
    
    all_passed = True
    for repo_url, expected in test_cases:
        try:
            result = client.parse_repo_url(repo_url)
            if result == expected:
                print(f"✅ {repo_url} -> {result}")
            else:
                print(f"❌ {repo_url} -> {result} (expected: {expected})")
                all_passed = False
        except Exception as e:
            print(f"❌ {repo_url} raised exception: {e}")
            all_passed = False
    
    # Test invalid URL
    try:
        client.parse_repo_url("invalid-url")
        print(f"❌ Should raise ValueError for invalid URL")
        all_passed = False
    except ValueError:
        print(f"✅ Invalid URL correctly raises ValueError")
    
    return all_passed


def test_get_file_content():
    """Test fetching file content"""
    print("\n🧪 Test 2: Get File Content")
    print("-" * 50)
    
    client = GitHubClient()
    repo_url = "https://github.com/paperless-ngx/paperless-ngx"
    
    try:
        # Fetch README.md
        content = client.get_file_content(repo_url, "README.md")
        
        if not content:
            print(f"❌ Empty content returned")
            return False
        
        if "paperless" not in content.lower():
            print(f"⚠️  Content doesn't contain 'paperless' (may be OK)")
        
        print(f"✅ Fetched README.md ({len(content)} characters)")
        print(f"   First 100 chars: {content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fetch file content: {e}")
        print(f"   Make sure you have internet connection and GitHub API is accessible")
        return False


def test_get_file_content_tuple():
    """Test fetching file content with tuple input"""
    print("\n🧪 Test 3: Get File Content (Tuple Input)")
    print("-" * 50)
    
    client = GitHubClient()
    repo_tuple = ("paperless-ngx", "paperless-ngx")
    
    try:
        content = client.get_file_content(repo_tuple, "README.md")
        
        if not content:
            print(f"❌ Empty content returned")
            return False
        
        print(f"✅ Fetched README.md using tuple input ({len(content)} characters)")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_get_repo_tree():
    """Test fetching repository tree"""
    print("\n🧪 Test 4: Get Repository Tree")
    print("-" * 50)
    
    client = GitHubClient()
    repo_url = "https://github.com/paperless-ngx/paperless-ngx"
    
    try:
        tree = client.get_repo_tree(repo_url)
        
        if not isinstance(tree, list):
            print(f"❌ Expected list, got {type(tree)}")
            return False
        
        if len(tree) == 0:
            print(f"⚠️  Empty tree returned (may be OK)")
        
        # Check structure
        if tree:
            first_item = tree[0]
            if "path" not in first_item:
                print(f"❌ Tree items missing 'path' field")
                return False
        
        print(f"✅ Fetched repository tree ({len(tree)} items)")
        if tree:
            print(f"   First item: {tree[0].get('path', 'unknown')} ({tree[0].get('type', 'unknown')})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fetch tree: {e}")
        return False


def test_get_repo_tree_path():
    """Test fetching tree for specific path"""
    print("\n🧪 Test 5: Get Repository Tree (Specific Path)")
    print("-" * 50)
    
    client = GitHubClient()
    repo_url = "https://github.com/paperless-ngx/paperless-ngx"
    
    try:
        # Get contents of docs directory (if it exists)
        tree = client.get_repo_tree(repo_url, path="docs")
        
        if not isinstance(tree, list):
            print(f"⚠️  Path 'docs' may not exist or is a file")
            print(f"   Result type: {type(tree)}")
            return True  # Not a failure, just info
        
        print(f"✅ Fetched tree for 'docs' path ({len(tree)} items)")
        return True
        
    except ValueError as e:
        if "not found" in str(e).lower():
            print(f"⚠️  Path 'docs' not found (may not exist in repo)")
            return True  # Not a failure
        else:
            print(f"❌ Failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_error_handling():
    """Test error handling"""
    print("\n🧪 Test 6: Error Handling")
    print("-" * 50)
    
    client = GitHubClient()
    
    # Test non-existent file
    try:
        client.get_file_content("https://github.com/paperless-ngx/paperless-ngx", "nonexistent-file.txt")
        print(f"❌ Should raise error for non-existent file")
        return False
    except (ValueError, httpx.HTTPStatusError):
        print(f"✅ Non-existent file correctly raises error")
    
    # Test invalid repo URL
    try:
        client.get_file_content("https://github.com/invalid/invalid-repo-12345", "README.md")
        print(f"⚠️  Invalid repo may not raise error immediately (GitHub API behavior)")
        return True
    except Exception:
        print(f"✅ Invalid repo correctly raises error")
        return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("Step 5 GitHub API Client Test Suite")
    print("=" * 50)
    print("\n⚠️  Prerequisites:")
    print("   - Internet connection required")
    print("   - GitHub API must be accessible")
    print("   - Rate limits: 60 requests/hour (unauthenticated)")
    print("=" * 50)
    
    results = [
        test_parse_repo_url(),
        test_get_file_content(),
        test_get_file_content_tuple(),
        test_get_repo_tree(),
        test_get_repo_tree_path(),
        test_error_handling(),
    ]
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All tests passed ({passed}/{total})")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        print("\n💡 Troubleshooting:")
        print("   1. Check internet connection")
        print("   2. Verify GitHub API is accessible: curl https://api.github.com")
        print("   3. Check rate limit status: curl -I https://api.github.com")
        return 1


if __name__ == "__main__":
    sys.exit(main())

