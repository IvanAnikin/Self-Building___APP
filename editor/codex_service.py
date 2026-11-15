"""
Codex Service for Self-Building App
Delegates feature implementation to OpenAI Codex CLI (non-interactive mode).
"""

import subprocess
import json
import os
import stat
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.conf import settings


class CodexService:
    """
    Wraps OpenAI Codex CLI to implement features via `codex exec`.
    
    Codex runs in a sandboxed subprocess with full file I/O,
    reads all relevant project files, makes surgical edits,
    and returns structured output.
    """
    
    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else Path(settings.BASE_DIR)
        self.api_key = os.environ.get('CODEX_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
        self.timeout = getattr(settings, 'CODEX_TIMEOUT', 300)  # 5 min default
        self.sandbox_mode = getattr(settings, 'CODEX_SANDBOX_MODE', 'workspace-write')
    
    # Protected files that Codex should never modify
    PROTECTED_FILES = [
        'manage.py',
        'selfbuilding_app/settings.py',
        'editor/codex_service.py',
        'editor/ai_service.py',
    ]
    
    def is_available(self) -> bool:
        """Check if codex CLI is installed and API key is configured."""
        if not self.api_key:
            return False
        try:
            result = subprocess.run(
                ['codex', '--version'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def implement(
        self,
        feature_description: str,
        implementation_plan: str,
        files_to_modify: List[str],
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delegate feature implementation to Codex CLI.
        
        Args:
            feature_description: Natural language description of the feature.
            implementation_plan: JSON string of the analysis result.
            files_to_modify: Hint list from the analysis step (Codex may
                             discover additional files on its own).
            working_dir: Override working directory (for per-user workspaces).
        
        Returns:
            {
                'success': bool,
                'files_changed': [
                    {
                        'file': 'relative/path.ext',
                        'code': 'new file content',
                        'changes': ['description of change 1', ...],
                        'notes': 'optional notes'
                    },
                    ...
                ],
                'summary': str,        # Codex's final message
                'events': list,        # Raw JSONL events (for debugging)
                'token_usage': {       # From turn.completed events
                    'input_tokens': int,
                    'output_tokens': int,
                    'cached_input_tokens': int
                },
                'error': str           # Only if success=False
            }
        """
        cwd = Path(working_dir) if working_dir else self.project_dir
        
        # Build the prompt
        prompt = self._build_prompt(feature_description, implementation_plan, files_to_modify)
        
        # Protect critical files before Codex runs
        self._protect_files(cwd)
        
        # Snapshot files BEFORE codex runs (for diff generation later)
        file_snapshots_before = self._snapshot_files(cwd, files_to_modify)
        
        try:
            # Run codex exec
            raw_result = self._run_codex(prompt, cwd)
            
            if not raw_result['success']:
                return {
                    'success': False,
                    'files_changed': [],
                    'summary': '',
                    'events': raw_result.get('events', []),
                    'token_usage': {},
                    'error': raw_result.get('error', 'Codex execution failed')
                }
            
            # Detect which files actually changed by comparing snapshots
            files_changed = self._detect_changes(cwd, file_snapshots_before)
            
            # Parse events for token usage and summary
            summary = self._extract_summary(raw_result['events'])
            token_usage = self._extract_token_usage(raw_result['events'])
            
            return {
                'success': True,
                'files_changed': files_changed,
                'summary': summary,
                'events': raw_result['events'],
                'token_usage': token_usage,
                'error': None
            }
        finally:
            # Always restore file permissions
            self._unprotect_files(cwd)
    
    def _build_prompt(
        self,
        description: str,
        plan: str,
        files_hint: List[str]
    ) -> str:
        """Build the prompt string for codex exec."""
        
        # Parse the plan JSON for a cleaner prompt
        try:
            plan_data = json.loads(plan)
            plan_steps = plan_data.get('plan', [])
            if isinstance(plan_steps, list):
                plan_text = '\n'.join(f'  {i+1}. {step}' for i, step in enumerate(plan_steps))
            else:
                plan_text = str(plan_steps)
        except (json.JSONDecodeError, TypeError):
            plan_text = str(plan)
        
        files_text = '\n'.join(f'  - {f}' for f in files_hint) if files_hint else '  (determine from codebase)'
        
        prompt = f"""Implement the following feature in this Django web application.

FEATURE REQUEST:
{description}

IMPLEMENTATION PLAN:
{plan_text}

FILES LIKELY NEEDING CHANGES (you may discover more):
{files_text}

CRITICAL RULES:
- Read each file BEFORE editing it to understand existing code.
- If you add CSS classes in an HTML template, you MUST also add the corresponding
  CSS rules in static/css/style.css.
- If you add HTML elements with IDs, check if static/js/main.js needs updates.
- Preserve ALL existing functionality — do not remove or break working code.
- Make minimal, surgical changes — do not rewrite entire files.
- After editing, verify your changes are consistent across all files.
- Follow the existing code style and naming conventions in each file.
"""
        return prompt
    
    def _run_codex(self, prompt: str, cwd: Path) -> Dict[str, Any]:
        """
        Execute `codex exec` as a subprocess.
        
        Returns:
            {
                'success': bool,
                'events': list,   # parsed JSONL events
                'error': str      # stderr or error message
            }
        """
        env = os.environ.copy()
        env['CODEX_API_KEY'] = self.api_key
        
        cmd = [
            'codex', 'exec',
            '--full-auto',
            '--sandbox', self.sandbox_mode,
            '--json',
            prompt
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                env=env,
                timeout=self.timeout
            )
            
            # Parse JSONL stdout
            events = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip non-JSON lines
            
            if result.returncode != 0 and not events:
                return {
                    'success': False,
                    'events': events,
                    'error': result.stderr or f'codex exec exited with code {result.returncode}'
                }
            
            # Check for error events
            error_events = [e for e in events if e.get('type') == 'error']
            if error_events:
                return {
                    'success': False,
                    'events': events,
                    'error': error_events[0].get('message', 'Unknown Codex error')
                }
            
            return {
                'success': True,
                'events': events,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'events': [],
                'error': f'Codex timed out after {self.timeout} seconds'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'events': [],
                'error': 'codex CLI not found. Install with: npm install -g @openai/codex'
            }
        except Exception as e:
            return {
                'success': False,
                'events': [],
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _snapshot_files(self, cwd: Path, files_hint: List[str]) -> Dict[str, Optional[str]]:
        """
        Read current content of files before Codex modifies them.
        Also snapshots common files that Codex might touch.
        """
        # Always include the common frontend/backend files
        all_files = set(files_hint or [])
        all_files.update([
            'editor/templates/editor/index.html',
            'static/css/style.css',
            'static/js/main.js',
            'editor/views.py',
            'editor/models.py',
            'editor/urls.py',
        ])
        
        snapshots = {}
        for rel_path in all_files:
            full_path = cwd / rel_path
            if full_path.exists():
                try:
                    snapshots[rel_path] = full_path.read_text(encoding='utf-8')
                except Exception:
                    snapshots[rel_path] = None
            else:
                snapshots[rel_path] = None  # File doesn't exist yet
        
        return snapshots
    
    def _detect_changes(
        self,
        cwd: Path,
        before_snapshots: Dict[str, Optional[str]]
    ) -> List[Dict[str, Any]]:
        """
        Compare file contents after Codex ran to detect what changed.
        
        Returns list of changed files in the format expected by the
        existing preview/apply pipeline.
        """
        changes = []
        
        for rel_path, before_content in before_snapshots.items():
            full_path = cwd / rel_path
            
            if not full_path.exists():
                # File existed before but was deleted — unusual, skip
                if before_content is not None:
                    continue
                # File still doesn't exist — no change
                continue
            
            try:
                after_content = full_path.read_text(encoding='utf-8')
            except Exception:
                continue
            
            # Compare
            if after_content != before_content:
                changes.append({
                    'file': rel_path,
                    'code': after_content,
                    'changes': [f'Modified by Codex'],
                    'notes': ''
                })
        
        # Also check for any NEW files created by Codex
        # (use git status to find untracked files)
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(cwd),
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    status = line[:2].strip()
                    file_path = line[3:].strip()
                    if status == '??' and file_path not in before_snapshots:
                        # New untracked file
                        full = cwd / file_path
                        if full.exists():
                            try:
                                changes.append({
                                    'file': file_path,
                                    'code': full.read_text(encoding='utf-8'),
                                    'changes': ['New file created by Codex'],
                                    'notes': 'This is a new file'
                                })
                            except Exception:
                                pass
        except Exception:
            pass
        
        return changes
    
    def _extract_summary(self, events: list) -> str:
        """Extract the final agent message from Codex JSONL events."""
        messages = [
            e.get('item', {}).get('text', '')
            for e in events
            if (e.get('type') == 'item.completed'
                and e.get('item', {}).get('type') == 'agent_message')
        ]
        return messages[-1] if messages else ''
    
    def _extract_token_usage(self, events: list) -> Dict[str, int]:
        """Extract total token usage from turn.completed events."""
        total = {'input_tokens': 0, 'output_tokens': 0, 'cached_input_tokens': 0}
        for e in events:
            if e.get('type') == 'turn.completed':
                usage = e.get('usage', {})
                total['input_tokens'] += usage.get('input_tokens', 0)
                total['output_tokens'] += usage.get('output_tokens', 0)
                total['cached_input_tokens'] += usage.get('cached_input_tokens', 0)
        return total
    
    def _protect_files(self, cwd: Path) -> None:
        """Make critical files read-only before Codex runs."""
        for rel_path in self.PROTECTED_FILES:
            full_path = cwd / rel_path
            if full_path.exists():
                try:
                    os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                except Exception:
                    pass  # Silently skip if permissions can't be changed
    
    def _unprotect_files(self, cwd: Path) -> None:
        """Restore write permissions after Codex runs."""
        for rel_path in self.PROTECTED_FILES:
            full_path = cwd / rel_path
            if full_path.exists():
                try:
                    os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                except Exception:
                    pass  # Silently skip if permissions can't be changed


# Singleton instance
codex_service = CodexService()
