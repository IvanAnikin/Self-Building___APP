# Codex Implementer — Technical Specification

> **Status:** Draft  
> **Author:** Auto-generated from codebase analysis  
> **Date:** February 2026  
> **Scope:** Replace the current `FeatureImplementer.generate_code()` pipeline with OpenAI Codex CLI delegation

---

## Table of Contents

1. [Objective](#1-objective)
2. [Current System Inventory](#2-current-system-inventory)
3. [What Gets Replaced vs. What Stays](#3-what-gets-replaced-vs-what-stays)
4. [Prerequisites & Dependencies](#4-prerequisites--dependencies)
5. [New Module: `codex_service.py`](#5-new-module-codex_servicepy)
6. [Changes to Existing Files](#6-changes-to-existing-files)
7. [AGENTS.md — Project Instructions for Codex](#7-agentsmd--project-instructions-for-codex)
8. [Security & Sandboxing](#8-security--sandboxing)
9. [Error Handling & Fallback](#9-error-handling--fallback)
10. [Database Schema Changes](#10-database-schema-changes)
11. [Frontend Changes](#11-frontend-changes)
12. [Configuration & Environment Variables](#12-configuration--environment-variables)
13. [Testing Plan](#13-testing-plan)
14. [Deployment Considerations](#14-deployment-considerations)
15. [Implementation Checklist](#15-implementation-checklist)

---

## 1. Objective

Replace the current per-file, isolated `FeatureImplementer.generate_code()` calls with a single invocation of `codex exec` that:

- Reads all relevant files on its own (full context awareness)
- Makes surgical edits across multiple files in one pass
- Validates its own work (runs syntax checks, optionally tests)
- Produces a machine-readable JSON stream of all changes made

The existing user-facing workflow (chat → detect → analyze → preview diff → approve/reject → git commit) remains **identical**. Only the internal code generation engine changes.

---

## 2. Current System Inventory

### Files Involved in Feature Implementation

| File | Role | Lines |
|------|------|-------|
| `editor/feature_implementer.py` | Code generation engine (to be partially replaced) | 628 |
| `editor/views.py` | API views: `analyze_feature`, `implement_feature`, `apply_feature_changes` | 961 |
| `editor/ai_service.py` | OpenAI API client singleton | 155 |
| `editor/git_service.py` | Per-user git branch management | 293 |
| `editor/models.py` | `FeatureRequest`, `FeatureVersion`, `TestResult` models | 170 |
| `static/js/main.js` | Frontend: `implementFeature()`, `reviewFeatureChanges()`, `approveFeatureChanges()` | 753 |
| `selfbuilding_app/urls.py` | API routes: `/api/features/analyze/`, `/api/features/implement/`, etc. | 51 |

### Current API Call Chain (what happens today)

```
Frontend                          Backend                           OpenAI API
────────                          ───────                           ──────────
POST /api/chat/
  {"message": "add X"}
                          ──→ _is_feature_request() 
                              FeatureRequest.create(status='pending')
                          ←── {"feature_request_id": 42}

User clicks "🚀 Implement"

POST /api/features/analyze/
  {"feature_id": 42}
                          ──→ feature_implementer.analyze_feature_request()
                              scan_project_structure()           ──→ os.walk()
                                                                 ──→ API call #1
                                                                     model: gpt-5.2
                                                                     tokens: 1,000
                                                                     sends: file NAMES only
                                                                 ←── JSON: plan + files_to_modify
                          ←── {"analysis": {feasible, plan, files_to_modify}}

POST /api/features/implement/
  {"feature_id": 42}
                          ──→ FOR EACH file in files_to_modify:
                                read_file_safely(file)           ──→ disk read
                                feature_implementer.generate_code()
                                                                 ──→ API call #N
                                                                     model: gpt-5.2
                                                                     tokens: 4,000
                                                                     sends: ONE file's content
                                                                 ←── JSON: complete new file
                              store all in feature.generated_code
                          ←── {"generated_files": [...]}

POST /api/features/preview/
  {"feature_id": 42}
                          ──→ generate_diff() per file
                          ←── {"previews": [diffs]}

User clicks "✅ Accept"

POST /api/features/apply/
  {"feature_id": 42}
                          ──→ FOR EACH file in generated_files:
                                apply_changes(file, content)     ──→ backup + overwrite
                              GitService.commit_changes()        ──→ git add + commit
                              FeatureVersion.create()
                          ←── {"applied_files": [...]}
```

### What's Wrong (Quick Summary)

| Problem | Impact |
|---------|--------|
| Each file generated in isolation — no cross-file context | CSS classes used in HTML never get defined in CSS |
| Full file replacement — AI returns entire file as JSON string | 4,000 token limit can't hold 937-line CSS file |
| No validation after generation | Broken code reaches the user preview |
| No iterative repair | One-shot generation, no test→fix loop |
| `files_to_modify` list may be incomplete | AI might omit `style.css` for a UI feature |

---

## 3. What Gets Replaced vs. What Stays

### ✅ Keeps (unchanged)

| Component | Why |
|-----------|-----|
| `_is_feature_request()` in views.py | Detection heuristic is independent of generation engine |
| `analyze_feature()` view + `analyze_feature_request()` method | Analysis/planning step stays — we'll feed the plan to Codex |
| `preview_feature_changes()` view | Still generates diffs from before/after snapshots |
| `apply_feature_changes()` view | Still overwrites files + git commits (but now from Codex output) |
| `reject_feature_changes()` view | Unchanged |
| `GitService` | Unchanged — still manages per-user branches |
| `FeatureRequest` / `FeatureVersion` / `TestResult` models | Schema stays, minor field additions |
| Frontend `main.js` — entire UI flow | Unchanged — same buttons, same modal, same diff view |
| `/api/features/analyze/`, `/api/features/preview/`, `/api/features/apply/`, `/api/features/reject/` | Routes unchanged |

### 🔄 Modified

| Component | Change |
|-----------|--------|
| `implement_feature()` in views.py | Replace the per-file `generate_code()` loop with a single `CodexService.implement()` call |
| `feature_implementer.py` | Keep `scan_project_structure()`, `read_file_safely()`, `generate_diff()`, `apply_changes()`. Remove or deprecate `generate_code()`. |
| `settings.py` | Add `CODEX_API_KEY`, `CODEX_TIMEOUT`, `CODEX_SANDBOX_MODE` settings |
| `requirements.txt` | No Python packages needed (Codex is a system binary), but document the dependency |

### 🆕 New Files

| File | Purpose |
|------|---------|
| `editor/codex_service.py` | New module — wraps `codex exec` subprocess calls |
| `AGENTS.md` (project root) | Instructions file that Codex reads to understand the project |

---

## 4. Prerequisites & Dependencies

### System Requirements

| Requirement | Version | Install Command |
|-------------|---------|-----------------|
| Node.js | 18+ | `brew install node` or system package manager |
| OpenAI Codex CLI | latest | `npm install -g @openai/codex` |
| Git | 2.23+ | Already present (Phase 5) |

### Authentication

Codex CLI authenticates via `CODEX_API_KEY` environment variable when used in non-interactive (`codex exec`) mode.

```bash
# .env file
CODEX_API_KEY=sk-...         # OpenAI API key for Codex
OPENAI_API_KEY=sk-...        # Existing key for chat/analysis (can be the same key)
```

**Important:** `CODEX_API_KEY` is only supported in `codex exec` mode. For interactive mode, you must run `codex` and sign in with ChatGPT. For our server integration, we always use `codex exec` with the API key.

### Verify Installation

```bash
# Check Codex is available
codex --version

# Test non-interactive mode
CODEX_API_KEY=sk-... codex exec --ephemeral "echo hello from codex"
```

---

## 5. New Module: `codex_service.py`

### Location

```
editor/codex_service.py
```

### Class Design

```python
"""
Codex Service for Self-Building App
Delegates feature implementation to OpenAI Codex CLI (non-interactive mode).
"""

import subprocess
import json
import os
import tempfile
import shutil
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
        
        # Snapshot files BEFORE codex runs (for diff generation later)
        file_snapshots_before = self._snapshot_files(cwd, files_to_modify)
        
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


# Singleton instance
codex_service = CodexService()
```

### Method Contract Summary

| Method | Input | Output | Side Effects |
|--------|-------|--------|-------------|
| `is_available()` | — | `bool` | None (checks system) |
| `implement()` | description, plan, files_hint | `{success, files_changed, summary, events, token_usage, error}` | **Codex edits files on disk** |
| `_build_prompt()` | description, plan, files_hint | `str` (prompt text) | None |
| `_run_codex()` | prompt, cwd | `{success, events, error}` | Spawns subprocess |
| `_snapshot_files()` | cwd, files_hint | `{path: content}` | Reads files |
| `_detect_changes()` | cwd, before_snapshots | `[{file, code, changes, notes}]` | Reads files + git status |

### Critical Design Decisions

**1. Snapshot-based change detection (not relying on Codex events)**

The `--json` event stream from `codex exec` includes `file_change` events, but these can be unreliable (partial events, rewritten files). Instead, we:
- Snapshot all relevant files BEFORE Codex runs
- Let Codex run with `--full-auto` (it edits files directly on disk)
- Compare snapshots AFTER to detect exactly what changed

This is more robust and produces the exact `{file, code}` format that the existing `preview_feature_changes()` and `apply_feature_changes()` views expect.

**2. Codex writes to a working copy, NOT directly to the live project**

For multi-user safety, Codex should operate on the user's git branch. The flow is:

```
1. GitService.checkout_branch()          ← switch to user-N-workspace
2. codex_service.implement()             ← Codex edits files on this branch
3. Detect changes (snapshot diff)
4. GitService.checkout_branch('main')    ← switch back to main
5. Store changes in feature.generated_code (JSON)
6. User previews diff
7. On approve: apply changes + commit on user branch
```

**However** — since the current app is single-repo and all users share the same filesystem, the simpler initial approach is:

```
1. Snapshot files before
2. Run Codex (it edits files in place)
3. Detect what changed
4. REVERT all files to their snapshots (undo Codex's edits)
5. Store the "after" content in feature.generated_code
6. User previews diff (from stored data, same as today)
7. On approve: write the stored content + git commit
```

This preserves the existing approve/reject workflow exactly.

**3. Fallback to old pipeline if Codex is unavailable**

If `codex_service.is_available()` returns `False` (CLI not installed, no API key), the system falls back to the existing `feature_implementer.generate_code()` per-file loop. Zero disruption.

---

## 6. Changes to Existing Files

### 6.1 `editor/views.py` — `implement_feature()` function

**Current** (lines 446-560): loops through `files_to_modify`, calls `feature_implementer.generate_code()` per file.

**New**: single call to `codex_service.implement()`, with fallback.

```python
# ADD at top of file:
from .codex_service import codex_service

# REPLACE the implement_feature function body (inside the try block, 
# after parsing files_to_modify from plan_data):

            # --- NEW: Codex-based implementation ---
            if codex_service.is_available():
                print("🤖 Using Codex CLI for implementation...")
                
                # Snapshot files before Codex edits them
                snapshots_before = codex_service._snapshot_files(
                    codex_service.project_dir, files_to_modify
                )
                
                codex_result = codex_service.implement(
                    feature_description=feature.description,
                    implementation_plan=feature.implementation_plan,
                    files_to_modify=files_to_modify
                )
                
                if codex_result['success'] and codex_result['files_changed']:
                    generated_files = codex_result['files_changed']
                    
                    # Revert Codex's disk changes (restore snapshots)
                    # so the approve/reject workflow stays intact
                    for rel_path, original_content in snapshots_before.items():
                        full_path = codex_service.project_dir / rel_path
                        if original_content is not None:
                            full_path.write_text(original_content, encoding='utf-8')
                    
                    print(f"✅ Codex generated changes for {len(generated_files)} file(s)")
                    if codex_result.get('summary'):
                        print(f"📝 Codex summary: {codex_result['summary'][:200]}")
                    if codex_result.get('token_usage'):
                        usage = codex_result['token_usage']
                        print(f"📊 Tokens: {usage.get('input_tokens',0)} in, "
                              f"{usage.get('output_tokens',0)} out")
                else:
                    # Codex failed — fall through to legacy pipeline
                    print(f"⚠️ Codex failed: {codex_result.get('error')}")
                    print("⬇️ Falling back to legacy per-file generation...")
                    generated_files = None
            else:
                print("⚠️ Codex not available, using legacy pipeline")
                generated_files = None
            
            # --- FALLBACK: Legacy per-file generation ---
            if generated_files is None:
                generated_files = []
                max_files_to_process = 5
                for file_path in files_to_modify[:max_files_to_process]:
                    # ... existing per-file generate_code() loop (unchanged) ...
```

### 6.2 `selfbuilding_app/settings.py` — New Settings

```python
# Codex CLI Configuration
CODEX_API_KEY = os.environ.get('CODEX_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
CODEX_TIMEOUT = int(os.environ.get('CODEX_TIMEOUT', '300'))       # seconds
CODEX_SANDBOX_MODE = os.environ.get('CODEX_SANDBOX_MODE', 'workspace-write')
```

### 6.3 `requirements.txt` — Documentation Addition

```
Django>=4.2.0
openai>=1.0.0
python-dotenv>=1.0.0

# System dependency (not a pip package):
# OpenAI Codex CLI — install with: npm install -g @openai/codex
# Required for AI-powered feature implementation (Phase 6)
```

### 6.4 `editor/feature_implementer.py` — No Deletion, Add Deprecation

Keep the entire file as-is for fallback. Add a comment at the top of `generate_code()`:

```python
    def generate_code(self, ...):
        """
        [DEPRECATED — Phase 6] Single-file code generation via OpenAI chat completion.
        
        This method generates code for ONE file at a time with no cross-file context.
        It is retained as a fallback when Codex CLI is not available.
        Prefer codex_service.implement() for multi-file, context-aware generation.
        """
```

---

## 7. AGENTS.md — Project Instructions for Codex

Codex CLI reads `AGENTS.md` from the repository root before executing any task. This file teaches Codex about the project structure, conventions, and rules.

### Location

```
AGENTS.md   (project root)
```

### Content

```markdown
# Self-Building App — Agent Instructions

## Project Overview
This is a Django web application ("Self-Building App") that includes a code editor,
AI chatbot, code execution engine, and AI-powered self-modification capability.

## Tech Stack
- Backend: Django 4.2+ / Python 3.9+
- Frontend: Vanilla HTML, CSS, JavaScript (no framework)
- Database: SQLite via Django ORM
- AI: OpenAI API (GPT models)
- Version Control: Git (per-user branches)

## Project Structure

### Key Files
- `editor/templates/editor/index.html` — Main (and only) HTML template
- `static/css/style.css` — All application styles (~937 lines)
- `static/js/main.js` — All frontend JavaScript (~753 lines)
- `editor/views.py` — All API views and auth views (~961 lines)
- `editor/models.py` — All Django models
- `editor/urls.py` — App-level URL routing
- `selfbuilding_app/urls.py` — Project-level URL routing

### File Relationships
- HTML template uses classes defined in `style.css`
- HTML template references IDs used by `main.js` (querySelector, getElementById)
- `main.js` calls API endpoints defined in `views.py`
- `views.py` uses models from `models.py`

## Critical Rules

### CSS ↔ HTML Consistency
- If you add a CSS class to any HTML element, you MUST define that class in
  `static/css/style.css`.
- If you remove an HTML element, check if its CSS rules should be removed.
- The existing layout uses `display: flex` on `.main-content` (line ~108 of style.css).

### JavaScript ↔ HTML Consistency
- If you add an HTML element with an `id`, check if `main.js` needs to reference it.
- If you change an element's `id`, update all `getElementById()` and `querySelector()`
  calls in `main.js`.

### Django Conventions
- All views use `@login_required` decorator.
- All model queries filter by `user=request.user` for data isolation.
- API views return `JsonResponse` with `{'status': 'success'|'error', ...}`.
- CSRF token is sent via `X-CSRFToken` header from frontend.

### Do NOT Modify
- `editor/codex_service.py` — The Codex integration service itself
- `editor/ai_service.py` — Chat AI service
- `selfbuilding_app/settings.py` — Django settings
- `manage.py`
- Any migration files
- Any `.backup` files

### Testing
- Run `python manage.py test editor` to check Django tests.
- The app runs on `http://127.0.0.1:8000`.

### Code Style
- Python: 4-space indentation, single quotes for strings, docstrings on all functions.
- JavaScript: 4-space indentation, single quotes, `async/await` for API calls.
- CSS: 4-space indentation, BEM-like class naming, all colors use CSS variables
  defined in `:root`.
```

---

## 8. Security & Sandboxing

### Codex Sandbox Modes

| Mode | What Codex Can Do | When to Use |
|------|-------------------|-------------|
| `read-only` (default) | Read files, run commands — no writes | Analysis-only tasks |
| `workspace-write` | Read + write files in the working directory | **Our default** — feature implementation |
| `danger-full-access` | Full system access | Never in production |

### Recommended: `workspace-write`

Codex can read and write any file in the project directory but cannot:
- Access files outside the project
- Install packages
- Run network commands
- Modify system files

### File Protection

The `AGENTS.md` file instructs Codex to never modify critical files (`settings.py`, `manage.py`, migrations). This is a soft guard — for hard protection, set files as read-only before running Codex:

```python
import os
import stat

PROTECTED_FILES = [
    'manage.py',
    'selfbuilding_app/settings.py',
    'editor/codex_service.py',
    'editor/ai_service.py',
]

def protect_files(project_dir):
    """Make critical files read-only before Codex runs."""
    for rel_path in PROTECTED_FILES:
        full_path = project_dir / rel_path
        if full_path.exists():
            os.chmod(full_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

def unprotect_files(project_dir):
    """Restore write permissions after Codex runs."""
    for rel_path in PROTECTED_FILES:
        full_path = project_dir / rel_path
        if full_path.exists():
            os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
```

### Multi-User Isolation (Future)

In production with multiple users, each user's Codex invocation should run in an isolated directory. Options:

1. **Git branch isolation** (current design) — checkout user branch, run Codex, capture changes, revert
2. **Copy-on-write workspace** — clone repo to `/tmp/user-N-workspace/`, run Codex there, copy results back
3. **Container isolation** — run `codex exec` inside a Docker container per user

For the initial implementation, option 1 (git branch + snapshot/revert) is sufficient.

---

## 9. Error Handling & Fallback

### Decision Flow

```
implement_feature() called
    │
    ├─ codex_service.is_available()?
    │      │
    │      ├─ YES ──→ codex_service.implement()
    │      │              │
    │      │              ├─ success + files_changed ──→ use Codex result
    │      │              │
    │      │              ├─ success + NO files_changed ──→ fallback
    │      │              │     (Codex ran but didn't edit anything)
    │      │              │
    │      │              └─ failure ──→ fallback + log error
    │      │
    │      └─ NO ──→ fallback (legacy per-file generation)
    │
    └─ fallback = existing feature_implementer.generate_code() loop
```

### Error Categories

| Error | Cause | Handling |
|-------|-------|----------|
| `FileNotFoundError` | `codex` binary not installed | `is_available()` returns False → fallback |
| `TimeoutExpired` | Codex took > 300s | Return error, revert snapshots, fallback |
| `returncode != 0` | Codex internal error | Parse events for error message, fallback |
| `error` event in JSONL | API error, auth failure, etc. | Extract message, log, fallback |
| Empty `files_changed` | Codex ran but made no edits | Treat as failure, fallback |
| Snapshot revert fails | File permission or I/O error | Log warning, files may be dirty |

### Logging

All Codex interactions are logged to Django's console logger:

```
🤖 Using Codex CLI for implementation...
📤 Prompt: "Implement the following feature..." (first 200 chars)
⏱️  Codex exec started (timeout: 300s, sandbox: workspace-write)
✅ Codex completed in 47s
📊 Tokens: 24,763 in (24,448 cached), 1,122 out
📁 Files changed: 3 (index.html, style.css, main.js)
📝 Summary: "I've implemented independent scrollable columns..."
```

---

## 10. Database Schema Changes

### No New Models Required

The existing `FeatureRequest` model already stores everything we need:

| Field | Current Use | New Use (Codex) |
|-------|-------------|-----------------|
| `generated_code` | JSON array of `{file, code, changes, notes}` | **Same format** — Codex output is normalized to match |
| `files_modified` | JSON list of file paths | Same |
| `implementation_plan` | JSON analysis from `analyze_feature_request()` | Same (still used to build Codex prompt) |
| `status` | pending → processing → completed/failed | Same state machine |
| `error_log` | Error message string | Same (Codex errors stored here) |
| `test_results_summary` | Test output | Same |

### Optional: Add `implementation_engine` Field

To track which engine generated the code (for analytics):

```python
# In FeatureRequest model — ADD:
implementation_engine = models.CharField(
    max_length=20,
    choices=[
        ('legacy', 'Legacy (per-file)'),
        ('codex', 'Codex CLI'),
    ],
    default='legacy',
    blank=True
)
```

Migration:
```bash
python manage.py makemigrations editor
python manage.py migrate
```

---

## 11. Frontend Changes

### None Required

The frontend is completely agnostic to the backend engine. The API contract is unchanged:

```
POST /api/features/implement/  →  {"generated_files": [{file, code, changes, notes}]}
POST /api/features/preview/    →  {"previews": [{file, diff, additions, deletions}]}
POST /api/features/apply/      →  {"applied_files": [{file, backup_created}]}
```

The `generated_files` format is identical whether produced by the legacy pipeline or Codex.

### Optional Enhancement: Show Engine Badge

Add a small badge in the review modal to indicate which engine generated the code:

```javascript
// In showDiffModal(), add to modal header:
const engineBadge = data.engine === 'codex'
    ? '<span class="badge codex-badge">🤖 Codex</span>'
    : '<span class="badge legacy-badge">⚙️ Legacy</span>';
```

This requires adding `engine` to the `/api/features/implement/` response:

```python
return JsonResponse({
    'status': 'success',
    'generated_files': generated_files,
    'feature_id': feature.id,
    'engine': 'codex' if used_codex else 'legacy'  # NEW
})
```

---

## 12. Configuration & Environment Variables

### `.env` File

```bash
# Existing
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.2
SECRET_KEY=your-django-secret-key
DEBUG=True

# New — Codex Integration
CODEX_API_KEY=sk-...              # Can be same as OPENAI_API_KEY
CODEX_TIMEOUT=300                 # Max seconds for codex exec (default: 300)
CODEX_SANDBOX_MODE=workspace-write # read-only | workspace-write | danger-full-access
```

### `settings.py` Additions

```python
# Phase 6: Codex CLI Configuration
CODEX_API_KEY = os.environ.get('CODEX_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
CODEX_TIMEOUT = int(os.environ.get('CODEX_TIMEOUT', '300'))
CODEX_SANDBOX_MODE = os.environ.get('CODEX_SANDBOX_MODE', 'workspace-write')
```

---

## 13. Testing Plan

### Unit Tests

| Test | What It Verifies |
|------|------------------|
| `test_codex_service_is_available_false` | Returns False when `codex` binary not found |
| `test_codex_service_is_available_no_key` | Returns False when API key is empty |
| `test_build_prompt_includes_description` | Prompt contains feature description |
| `test_build_prompt_includes_files` | Prompt lists files_to_modify |
| `test_build_prompt_includes_rules` | Prompt contains CSS/HTML consistency rules |
| `test_snapshot_files_reads_existing` | Correctly reads file content |
| `test_snapshot_files_handles_missing` | Returns None for non-existent files |
| `test_detect_changes_finds_modified` | Detects when file content differs from snapshot |
| `test_detect_changes_ignores_unchanged` | Skips files with identical content |
| `test_extract_summary_from_events` | Parses final agent_message from JSONL |
| `test_extract_token_usage` | Sums tokens from turn.completed events |

### Integration Tests (require Codex CLI installed)

| Test | What It Verifies |
|------|------------------|
| `test_implement_simple_css_change` | Codex adds a CSS rule when prompted |
| `test_implement_multi_file_feature` | Codex modifies HTML + CSS + JS together |
| `test_implement_revert_after_codex` | Snapshots are correctly restored after Codex runs |
| `test_fallback_when_codex_unavailable` | Legacy pipeline activates when Codex is missing |
| `test_full_workflow_with_codex` | Chat → detect → analyze → implement (Codex) → preview → apply → git commit |

### E2E Test Addition

Add to `e2e_test.py`:

```python
# TEST: Feature Implementation Engine
r = s2.post(f'{BASE}/api/features/implement/', headers=headers, json={
    'feature_id': feature_id
})
data = r.json()
assert data.get('status') == 'success'
assert len(data.get('generated_files', [])) > 0
print(f"Engine used: {data.get('engine', 'unknown')}")
```

---

## 14. Deployment Considerations

### Development (Local Mac)

```bash
# One-time setup
npm install -g @openai/codex
echo 'CODEX_API_KEY=sk-...' >> .env

# Verify
codex --version
source venv/bin/activate && python -c "
from editor.codex_service import codex_service
print(f'Codex available: {codex_service.is_available()}')
"
```

### Production (Linux Server)

```bash
# Install Node.js (if not present)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Codex CLI
npm install -g @openai/codex

# Set environment variables
export CODEX_API_KEY=sk-...
export CODEX_TIMEOUT=300
export CODEX_SANDBOX_MODE=workspace-write

# Run Django with Codex available
python manage.py runserver 0.0.0.0:8000
```

### Docker

```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g @openai/codex

ENV CODEX_API_KEY=""
ENV CODEX_TIMEOUT=300
ENV CODEX_SANDBOX_MODE=workspace-write
```

### Cost Estimation

| Operation | Approx. Cost (GPT-4.1 pricing) |
|-----------|-------------------------------|
| Feature analysis (1,000 tokens out) | ~$0.01 |
| Codex implementation (typical 5K-20K tokens) | ~$0.05 - $0.20 |
| Legacy per-file fallback (4K tokens × N files) | ~$0.02 - $0.08 |

Codex may cost slightly more per feature but produces significantly higher quality output, reducing the need for manual fixes.

---

## 15. Implementation Checklist

### Phase 6A — Core Integration

- [ ] Install Codex CLI on dev machine: `npm install -g @openai/codex`
- [ ] Add `CODEX_API_KEY` to `.env`
- [ ] Create `AGENTS.md` in project root
- [ ] Create `editor/codex_service.py` (the `CodexService` class)
- [ ] Add Codex settings to `selfbuilding_app/settings.py`
- [ ] Modify `implement_feature()` in `editor/views.py` to call `codex_service.implement()` with fallback
- [ ] Add deprecation docstring to `feature_implementer.generate_code()`
- [ ] Test: verify Codex is called when available
- [ ] Test: verify fallback works when Codex is unavailable
- [ ] Test: verify snapshot-revert cycle works (files restored after Codex runs)
- [ ] Test: verify generated_files format is compatible with preview/apply views

### Phase 6B — Hardening

- [ ] Add file protection (chmod read-only) for critical files before Codex runs
- [ ] Add `implementation_engine` field to `FeatureRequest` model + migration
- [ ] Add engine info to `/api/features/implement/` response
- [ ] Add logging for Codex token usage and timing
- [ ] Write unit tests for `CodexService` methods
- [ ] Write integration test for full feature workflow with Codex
- [ ] Update `e2e_test.py` with feature implementation test

### Phase 6C — Polish

- [ ] Add optional engine badge to frontend review modal
- [ ] Add Codex availability check to `/api/status/` health endpoint
- [ ] Document Codex setup in README.md
- [ ] Update `requirements.txt` with system dependency note
- [ ] Add Docker instructions for Codex CLI

---

*End of specification.*
