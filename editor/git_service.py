"""
Git Service for Phase 5: Version Control Integration

This service manages git operations for per-user version control:
- Creates user-specific branches
- Commits feature changes
- Manages version history
- Supports rollback to previous versions
"""

import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from django.conf import settings


class GitService:
    """Handles all git operations for user workspaces"""
    
    def __init__(self, user):
        self.user = user
        self.branch_name = f"user-{user.id}-workspace"
        self.repo_path = Path(settings.BASE_DIR)
    
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Execute a git command and return the result.
        
        Args:
            command: List of command arguments (e.g., ['git', 'status'])
            
        Returns:
            Dictionary with:
            {
                'success': bool,
                'stdout': str,
                'stderr': str,
                'returncode': int
            }
        """
        try:
            result = subprocess.run(
                command,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Git command timed out after 30 seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def initialize_repo(self) -> bool:
        """
        Initialize git repository if not already initialized.
        
        Returns:
            True if repo is initialized, False otherwise
        """
        # Check if .git directory exists
        git_dir = self.repo_path / '.git'
        if git_dir.exists():
            return True
        
        # Initialize git repo
        result = self._run_git_command(['git', 'init'])
        if not result['success']:
            print(f"Failed to initialize git: {result['stderr']}")
            return False
        
        # Configure user (for commits)
        self._run_git_command(['git', 'config', 'user.email', 'app@selfbuilding.local'])
        self._run_git_command(['git', 'config', 'user.name', 'Self-Building App'])
        
        # Create initial commit on main branch
        self._run_git_command(['git', 'add', '.'])
        result = self._run_git_command(['git', 'commit', '-m', 'Initial commit - Phase 5 baseline', '--allow-empty'])
        
        return result['success']
    
    def initialize_user_branch(self) -> bool:
        """
        Create user's branch if it doesn't exist.
        
        Returns:
            True if branch exists or was created, False on error
        """
        # Ensure repo is initialized
        if not self.initialize_repo():
            return False
        
        # Check if branch already exists
        result = self._run_git_command(['git', 'branch', '--list', self.branch_name])
        if self.branch_name in result['stdout']:
            print(f"Branch {self.branch_name} already exists")
            return True
        
        # Create and checkout new branch
        result = self._run_git_command(['git', 'checkout', '-b', self.branch_name])
        if not result['success']:
            print(f"Failed to create branch {self.branch_name}: {result['stderr']}")
            return False
        
        print(f"✅ Created branch: {self.branch_name}")
        return True
    
    def checkout_branch(self) -> bool:
        """
        Checkout user's branch.
        
        Returns:
            True if checkout succeeded, False otherwise
        """
        result = self._run_git_command(['git', 'checkout', self.branch_name])
        if not result['success']:
            print(f"Failed to checkout branch {self.branch_name}: {result['stderr']}")
            return False
        return True
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Optional[str]:
        """
        Commit changes to user's branch.
        
        Args:
            message: Commit message
            files: List of specific files to commit (None = all changes)
            
        Returns:
            Commit hash if successful, None otherwise
        """
        # Ensure we're on the right branch
        if not self.checkout_branch():
            return None
        
        # Add files
        if files:
            for file in files:
                self._run_git_command(['git', 'add', file])
        else:
            self._run_git_command(['git', 'add', '.'])
        
        # Commit
        full_message = f"{message} [user-{self.user.id}]"
        result = self._run_git_command(['git', 'commit', '-m', full_message])
        
        if not result['success']:
            print(f"Commit failed: {result['stderr']}")
            return None
        
        # Get commit hash
        hash_result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        if hash_result['success']:
            commit_hash = hash_result['stdout'].strip()
            print(f"✅ Committed: {commit_hash[:7]} - {message}")
            return commit_hash
        
        return None
    
    def get_commit_history(self, limit: int = 20) -> List[Dict[str, str]]:
        """
        Get commit history for user's branch.
        
        Args:
            limit: Maximum number of commits to return
            
        Returns:
            List of commit dictionaries with: hash, message, date, author
        """
        # Ensure we're on the right branch
        if not self.checkout_branch():
            return []
        
        # Get commit log
        format_string = "%H|%s|%ad|%an"
        result = self._run_git_command([
            'git', 'log',
            f'--max-count={limit}',
            '--date=short',
            f'--pretty=format:{format_string}'
        ])
        
        if not result['success']:
            return []
        
        commits = []
        for line in result['stdout'].strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                commits.append({
                    'hash': parts[0],
                    'message': parts[1],
                    'date': parts[2],
                    'author': parts[3]
                })
        
        return commits
    
    def checkout_commit(self, commit_hash: str) -> bool:
        """
        Checkout a specific commit (read-only view).
        
        Args:
            commit_hash: Commit hash to checkout
            
        Returns:
            True if successful, False otherwise
        """
        result = self._run_git_command(['git', 'checkout', commit_hash])
        if not result['success']:
            print(f"Failed to checkout commit {commit_hash}: {result['stderr']}")
            return False
        
        print(f"✅ Checked out commit: {commit_hash[:7]}")
        return True
    
    def rollback_to_commit(self, commit_hash: str) -> bool:
        """
        Hard reset to a previous commit (destructive!).
        
        Args:
            commit_hash: Commit hash to reset to
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure we're on the right branch
        if not self.checkout_branch():
            return False
        
        # Hard reset to commit
        result = self._run_git_command(['git', 'reset', '--hard', commit_hash])
        if not result['success']:
            print(f"Failed to rollback to {commit_hash}: {result['stderr']}")
            return False
        
        print(f"✅ Rolled back to commit: {commit_hash[:7]}")
        return True
    
    def get_current_commit(self) -> Optional[str]:
        """
        Get the current commit hash.
        
        Returns:
            Commit hash or None
        """
        result = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        if result['success']:
            return result['stdout'].strip()
        return None
    
    def get_changed_files(self) -> List[str]:
        """
        Get list of files that have uncommitted changes.
        
        Returns:
            List of file paths
        """
        result = self._run_git_command(['git', 'diff', '--name-only'])
        if result['success']:
            return [f for f in result['stdout'].strip().split('\n') if f]
        return []
    
    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.
        
        Returns:
            True if there are changes, False otherwise
        """
        result = self._run_git_command(['git', 'status', '--porcelain'])
        return bool(result['stdout'].strip())
