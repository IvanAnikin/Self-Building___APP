"""
Feature Implementer Module for Self-Building App
Provides AI-powered code generation and automated file modification.
"""

import os
import json
import subprocess
from typing import Dict, Any, List
from pathlib import Path
from .ai_service import ai_service


class FeatureImplementer:
    """
    Handles automated feature implementation through AI code generation
    and safe file system modifications.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the feature implementer.
        
        Args:
            base_path: Base directory for the project (default: current directory)
        """
        self.base_path = Path(base_path) if base_path else Path(os.getcwd())
        self.ai_service = ai_service
    
    def scan_project_structure(self) -> Dict[str, Any]:
        """
        Scan the project directory and return a comprehensive structure map.
        
        Returns:
            Dictionary containing:
            {
                'python_files': List[str],
                'templates': List[str],
                'static_files': List[str],
                'models': List[str],
                'views': List[str],
                'urls': List[str]
            }
        """
        structure = {
            'python_files': [],
            'templates': [],
            'static_files': [],
            'models': [],
            'views': [],
            'urls': []
        }
        
        # Scan Python files
        for root, dirs, files in os.walk(self.base_path):
            # Skip venv, migrations, __pycache__
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'migrations', '.git']]
            
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.base_path)
                
                if file.endswith('.py'):
                    structure['python_files'].append(rel_path)
                    if 'models.py' in file:
                        structure['models'].append(rel_path)
                    elif 'views.py' in file:
                        structure['views'].append(rel_path)
                    elif 'urls.py' in file:
                        structure['urls'].append(rel_path)
                
                elif file.endswith('.html'):
                    structure['templates'].append(rel_path)
                
                elif file.endswith(('.js', '.css', '.jpg', '.png', '.svg')):
                    structure['static_files'].append(rel_path)
        
        return structure
    
    def read_file_safely(self, file_path: str) -> Dict[str, Any]:
        """
        Safely read a file's content.
        
        Args:
            file_path: Relative path to file from project root
            
        Returns:
            Dictionary with:
            {
                'exists': bool,
                'content': str (if exists),
                'error': str (if failed)
            }
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return {
                    'exists': False,
                    'content': None,
                    'error': f'File {file_path} does not exist'
                }
            
            # Don't read binary files or very large files
            if full_path.stat().st_size > 500000:  # 500KB limit
                return {
                    'exists': True,
                    'content': None,
                    'error': 'File too large to read'
                }
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'exists': True,
                'content': content,
                'error': None
            }
            
        except Exception as e:
            return {
                'exists': False,
                'content': None,
                'error': f'Error reading file: {str(e)}'
            }
    
    def analyze_feature_request(self, description: str) -> Dict[str, Any]:
        """
        Analyze a feature request and create an implementation plan.
        
        Args:
            description: Natural language description of the feature
            
        Returns:
            Dictionary containing:
            {
                'feasible': bool,
                'plan': str,
                'files_to_modify': list,
                'estimated_complexity': str,
                'reason': str (if not feasible)
            }
        """
        if not self.ai_service.is_enabled():
            return {
                'feasible': False,
                'reason': 'AI service is not enabled. Please configure OpenAI API key.'
            }
        
        # Scan project structure for context
        project_structure = self.scan_project_structure()
        
        prompt = f"""Analyze the following feature request for a Django web application (Self-Building App):

Feature Request: {description}

Current Project Structure:
- Django backend (Python)
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Database: SQLite with Django ORM

Existing Files:
Python Files: {', '.join(project_structure['python_files'][:20])}
Templates: {', '.join(project_structure['templates'])}
Static Files: {', '.join(project_structure['static_files'][:20])}

Existing models: ChatMessage, CodeSnippet, FeatureRequest, CodeExecution
Existing features: Code editor, AI chatbot, Code execution (Python/JS)

IMPORTANT: Use ONLY the actual file paths listed above. Do not invent new file names.

Please provide:
1. Feasibility assessment (is this implementable?)
2. Implementation plan (step-by-step)
3. List of EXISTING files that need modification (choose from files listed above)
4. Estimated complexity (simple/medium/complex)
5. Any dependencies or prerequisites

Respond in JSON format:
{{
    "feasible": true/false,
    "plan": ["step 1", "step 2", ...],
    "files_to_modify": ["actual/file/path.py"],
    "estimated_complexity": "simple|medium|complex",
    "reason": "explanation if not feasible"
}}"""
        
        try:
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": "You are an expert software architect analyzing feature requests."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError as e:
                return {
                    'feasible': False,
                    'reason': f'AI response parsing error: {str(e)}'
                }
            
        except Exception as e:
            return {
                'feasible': False,
                'reason': f'Error analyzing request: {str(e)}'
            }
    
    def generate_code(self, feature_description: str, implementation_plan: str, 
                     target_file: str, existing_code: str = None) -> Dict[str, Any]:
        """
        Generate code for a specific file based on the feature request.
        
        Args:
            feature_description: Description of the feature
            implementation_plan: The implementation plan
            target_file: The file to generate/modify
            existing_code: Existing code content if modifying an existing file
            
        Returns:
            Dictionary with generated code and instructions
        """
        if not self.ai_service.is_enabled():
            return {
                'success': False,
                'error': 'AI service not enabled'
            }
        
        mode = "modify" if existing_code else "create"
        
        # Build existing code section separately to avoid f-string backslash issue
        existing_code_section = ""
        if existing_code:
            existing_code_section = f"""
Current File Content:
```
{existing_code}
```

IMPORTANT: Modify the existing code above to add the requested feature.
- Preserve all existing functionality
- Maintain existing imports, functions, and structure
- Only add/modify what's necessary for the new feature
- Keep the same file format and style
"""
        else:
            existing_code_section = """
This is a NEW file that does not exist yet.
Generate complete, production-ready code.
"""
        
        modified_or_new = "modified" if existing_code else "new"
        
        prompt = f"""Generate code for this Django application feature:

Feature: {feature_description}

Implementation Plan: {implementation_plan}

Target File: {target_file}
Mode: {mode}

{existing_code_section}

Generate the complete {modified_or_new} file content for {target_file}.
Follow Django best practices and maintain code quality.
Ensure the code integrates seamlessly with the existing application.

If modifying existing code:
- Preserve all critical functionality
- Keep existing imports and structure
- Comment your changes with # NEW: or # MODIFIED:

Respond in JSON format:
{{
    "code": "complete file content",
    "changes_made": ["list of key changes"],
    "notes": "important implementation notes",
    "preserved": ["list of things preserved from original"]
}}"""
        
        try:
            response = self.ai_service.client.chat.completions.create(
                model=self.ai_service.model,
                messages=[
                    {"role": "system", "content": "You are an expert Django developer generating production-ready code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                result['success'] = True
                return result
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'AI response parsing error: {str(e)}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Code generation error: {str(e)}'
            }
    
    def preview_changes(self, file_path: str, new_content: str) -> Dict[str, str]:
        """
        Generate a preview of changes to be made to a file.
        
        Args:
            file_path: Path to the file
            new_content: New content to be written
            
        Returns:
            Dictionary with 'before' and 'after' content
        """
        full_path = self.base_path / file_path
        
        if full_path.exists():
            with open(full_path, 'r') as f:
                before = f.read()
        else:
            before = "# New file - no previous content"
        
        return {
            'before': before,
            'after': new_content,
            'file_path': file_path
        }
    
    def apply_changes(self, file_path: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """
        Apply changes to a file with optional backup.
        
        Args:
            file_path: Relative path to the file
            content: New content to write
            backup: Whether to create a backup
            
        Returns:
            Dictionary with operation result
        """
        try:
            full_path = self.base_path / file_path
            
            # Track if backup was actually created
            backup_created = False
            
            # Create backup if requested and file exists
            if backup and full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                with open(full_path, 'r') as f:
                    with open(backup_path, 'w') as backup_f:
                        backup_f.write(f.read())
                backup_created = True
            
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write new content
            with open(full_path, 'w') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'Successfully updated {file_path}',
                'backup_created': backup_created
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply changes: {str(e)}'
            }
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run Django tests to validate changes.
        
        Returns:
            Dictionary with test results
        """
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'test', 'editor', '--verbosity', '0'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                timeout=120
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
                'error': 'Tests timed out after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Test execution error: {str(e)}'
            }
    
    def create_git_commit(self, message: str, files: List[str] = None) -> Dict[str, Any]:
        """
        Create a git commit for the changes.
        
        Args:
            message: Commit message
            files: List of files to commit (None for all changes)
            
        Returns:
            Dictionary with commit result
        """
        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(
                        ['git', 'add', file],
                        cwd=self.base_path,
                        check=True,
                        capture_output=True
                    )
            else:
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.base_path,
                    check=True,
                    capture_output=True
                )
            
            # Create commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Git commit failed',
                    'stderr': result.stderr
                }
            
            # Get commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hash = hash_result.stdout.strip()
            
            return {
                'success': True,
                'commit_hash': commit_hash,
                'message': message
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Git operation error: {str(e)}'
            }
    
    def rollback_changes(self, commit_hash: str = None, files: List[str] = None) -> Dict[str, Any]:
        """
        Rollback changes to a previous state.
        
        Args:
            commit_hash: Specific commit to rollback to (if None, rollback last commit)
            files: Specific files to rollback (if None, rollback all)
            
        Returns:
            Dictionary with rollback result
        """
        try:
            if commit_hash:
                # Reset to specific commit
                subprocess.run(
                    ['git', 'reset', '--hard', commit_hash],
                    cwd=self.base_path,
                    check=True,
                    capture_output=True
                )
            elif files:
                # Restore specific files
                subprocess.run(
                    ['git', 'restore', '--source=HEAD~1'] + files,
                    cwd=self.base_path,
                    check=True,
                    capture_output=True
                )
            else:
                # Revert last commit
                subprocess.run(
                    ['git', 'revert', '--no-commit', 'HEAD'],
                    cwd=self.base_path,
                    check=True,
                    capture_output=True
                )
            
            return {
                'success': True,
                'message': 'Changes rolled back successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Rollback error: {str(e)}'
            }


# Global instance
feature_implementer = FeatureImplementer()
