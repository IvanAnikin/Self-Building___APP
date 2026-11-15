"""
Unit tests for CodexService

Tests the Codex CLI integration service including:
- Availability checks
- Prompt building
- File snapshotting
- Change detection
- Event parsing
- File protection
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import subprocess
import tempfile
import os
import json
from django.test import TestCase
from django.conf import settings

from editor.codex_service import CodexService


class TestCodexServiceAvailability(TestCase):
    """Test is_available() method"""
    
    @patch('subprocess.run')
    def test_is_available_returns_false_when_no_binary(self, mock_run):
        """Test that is_available returns False when codex binary is not found"""
        mock_run.side_effect = FileNotFoundError()
        service = CodexService()
        service.api_key = 'test-key'
        self.assertFalse(service.is_available())
    
    def test_is_available_returns_false_when_no_api_key(self):
        """Test that is_available returns False when API key is empty"""
        service = CodexService()
        service.api_key = ''
        self.assertFalse(service.is_available())
    
    @patch('subprocess.run')
    def test_is_available_returns_true_when_configured(self, mock_run):
        """Test that is_available returns True when codex is installed and key is set"""
        mock_run.return_value = MagicMock(returncode=0)
        service = CodexService()
        service.api_key = 'test-key'
        self.assertTrue(service.is_available())
    
    @patch('subprocess.run')
    def test_is_available_handles_timeout(self, mock_run):
        """Test that is_available returns False on timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired('codex', 10)
        service = CodexService()
        service.api_key = 'test-key'
        self.assertFalse(service.is_available())


class TestCodexServicePromptBuilding(TestCase):
    """Test _build_prompt() method"""
    
    def test_build_prompt_contains_feature_description(self):
        """Test that the prompt includes the feature description"""
        service = CodexService()
        description = "Add a dark mode toggle button"
        plan = json.dumps({"plan": ["Step 1", "Step 2"], "feasible": True})
        files = ["static/css/style.css"]
        
        prompt = service._build_prompt(description, plan, files)
        
        self.assertIn(description, prompt)
    
    def test_build_prompt_contains_files_list(self):
        """Test that the prompt includes files_to_modify"""
        service = CodexService()
        description = "Add feature"
        plan = json.dumps({"plan": ["Step 1"], "feasible": True})
        files = ["editor/views.py", "static/js/main.js"]
        
        prompt = service._build_prompt(description, plan, files)
        
        for file in files:
            self.assertIn(file, prompt)
    
    def test_build_prompt_contains_critical_rules(self):
        """Test that the prompt contains CSS/HTML consistency rules"""
        service = CodexService()
        description = "Add feature"
        plan = json.dumps({"plan": ["Step 1"], "feasible": True})
        files = []
        
        prompt = service._build_prompt(description, plan, files)
        
        self.assertIn("CSS classes", prompt)
        self.assertIn("HTML", prompt)
        self.assertIn("CRITICAL RULES", prompt)
    
    def test_build_prompt_handles_invalid_json_plan(self):
        """Test that _build_prompt handles non-JSON plan gracefully"""
        service = CodexService()
        description = "Add feature"
        plan = "Not a JSON string"
        files = []
        
        prompt = service._build_prompt(description, plan, files)
        
        # Should not raise an exception, should fallback to string representation
        self.assertIn(description, prompt)


class TestCodexServiceSnapshotting(TestCase):
    """Test _snapshot_files() method"""
    
    def test_snapshot_files_reads_existing_files(self):
        """Test that snapshot_files correctly reads existing file content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test files
            test_file = tmpdir / "test.py"
            test_file.write_text("print('hello')")
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = service._snapshot_files(tmpdir, ["test.py"])
            
            self.assertIn("test.py", snapshots)
            self.assertEqual(snapshots["test.py"], "print('hello')")
    
    def test_snapshot_files_returns_none_for_missing(self):
        """Test that snapshot_files returns None for non-existent files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = service._snapshot_files(tmpdir, ["nonexistent.py"])
            
            self.assertIn("nonexistent.py", snapshots)
            self.assertIsNone(snapshots["nonexistent.py"])
    
    def test_snapshot_files_includes_common_files(self):
        """Test that snapshot_files includes common project files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = service._snapshot_files(tmpdir, [])
            
            # Should include common files even if not in hint list
            self.assertIn("static/css/style.css", snapshots)
            self.assertIn("static/js/main.js", snapshots)
            self.assertIn("editor/views.py", snapshots)


class TestCodexServiceChangeDetection(TestCase):
    """Test _detect_changes() method"""
    
    def test_detect_changes_finds_modified_files(self):
        """Test that detect_changes finds files that were modified"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a file and take snapshot
            test_file = tmpdir / "test.py"
            test_file.write_text("original content")
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = {"test.py": "original content"}
            
            # Modify the file
            test_file.write_text("modified content")
            
            changes = service._detect_changes(tmpdir, snapshots)
            
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]['file'], "test.py")
            self.assertEqual(changes[0]['code'], "modified content")
    
    def test_detect_changes_ignores_unchanged_files(self):
        """Test that detect_changes skips files with identical content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a file and take snapshot
            test_file = tmpdir / "test.py"
            test_file.write_text("same content")
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = {"test.py": "same content"}
            
            changes = service._detect_changes(tmpdir, snapshots)
            
            self.assertEqual(len(changes), 0)
    
    @patch('subprocess.run')
    def test_detect_changes_finds_new_files(self, mock_run):
        """Test that detect_changes finds new files created by Codex"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Mock git status to show a new file
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="?? newfile.py\n"
            )
            
            # Create the new file
            new_file = tmpdir / "newfile.py"
            new_file.write_text("new content")
            
            service = CodexService(project_dir=str(tmpdir))
            snapshots = {}
            
            changes = service._detect_changes(tmpdir, snapshots)
            
            # Should detect the new file
            new_files = [c for c in changes if c['file'] == 'newfile.py']
            self.assertEqual(len(new_files), 1)
            self.assertIn("New file created", new_files[0]['changes'][0])


class TestCodexServiceEventParsing(TestCase):
    """Test event parsing methods"""
    
    def test_extract_summary_from_events(self):
        """Test that extract_summary parses agent_message from JSONL events"""
        service = CodexService()
        events = [
            {
                'type': 'item.completed',
                'item': {
                    'type': 'agent_message',
                    'text': 'First message'
                }
            },
            {
                'type': 'item.completed',
                'item': {
                    'type': 'agent_message',
                    'text': 'Final summary message'
                }
            }
        ]
        
        summary = service._extract_summary(events)
        
        # Should return the last agent_message
        self.assertEqual(summary, 'Final summary message')
    
    def test_extract_summary_returns_empty_when_no_messages(self):
        """Test that extract_summary returns empty string when no messages"""
        service = CodexService()
        events = []
        
        summary = service._extract_summary(events)
        
        self.assertEqual(summary, '')
    
    def test_extract_token_usage_sums_correctly(self):
        """Test that extract_token_usage correctly sums tokens from events"""
        service = CodexService()
        events = [
            {
                'type': 'turn.completed',
                'usage': {
                    'input_tokens': 1000,
                    'output_tokens': 500,
                    'cached_input_tokens': 200
                }
            },
            {
                'type': 'turn.completed',
                'usage': {
                    'input_tokens': 1500,
                    'output_tokens': 600,
                    'cached_input_tokens': 300
                }
            }
        ]
        
        usage = service._extract_token_usage(events)
        
        self.assertEqual(usage['input_tokens'], 2500)
        self.assertEqual(usage['output_tokens'], 1100)
        self.assertEqual(usage['cached_input_tokens'], 500)
    
    def test_extract_token_usage_handles_missing_fields(self):
        """Test that extract_token_usage handles events without usage fields"""
        service = CodexService()
        events = [
            {'type': 'other_event'},
            {'type': 'turn.completed', 'usage': {'input_tokens': 100}}
        ]
        
        usage = service._extract_token_usage(events)
        
        self.assertEqual(usage['input_tokens'], 100)
        self.assertEqual(usage['output_tokens'], 0)
        self.assertEqual(usage['cached_input_tokens'], 0)


class TestCodexServiceRunCodex(TestCase):
    """Test _run_codex() method"""
    
    @patch('subprocess.run')
    def test_run_codex_handles_timeout(self, mock_run):
        """Test that _run_codex handles TimeoutExpired exception"""
        mock_run.side_effect = subprocess.TimeoutExpired('codex', 300)
        
        service = CodexService()
        service.api_key = 'test-key'
        result = service._run_codex("test prompt", Path.cwd())
        
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['error'])
    
    @patch('subprocess.run')
    def test_run_codex_handles_missing_binary(self, mock_run):
        """Test that _run_codex handles missing codex binary"""
        mock_run.side_effect = FileNotFoundError()
        
        service = CodexService()
        service.api_key = 'test-key'
        result = service._run_codex("test prompt", Path.cwd())
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
    
    @patch('subprocess.run')
    def test_run_codex_parses_jsonl_events(self, mock_run):
        """Test that _run_codex correctly parses JSONL output"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"type": "event1"}\n{"type": "event2"}\n',
            stderr=''
        )
        
        service = CodexService()
        service.api_key = 'test-key'
        result = service._run_codex("test prompt", Path.cwd())
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['events']), 2)
        self.assertEqual(result['events'][0]['type'], 'event1')
    
    @patch('subprocess.run')
    def test_run_codex_detects_error_events(self, mock_run):
        """Test that _run_codex detects error events in JSONL"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"type": "error", "message": "API error occurred"}\n',
            stderr=''
        )
        
        service = CodexService()
        service.api_key = 'test-key'
        result = service._run_codex("test prompt", Path.cwd())
        
        self.assertFalse(result['success'])
        self.assertIn('API error', result['error'])


class TestCodexServiceFileProtection(TestCase):
    """Test file protection methods"""
    
    def test_protect_files_makes_files_readonly(self):
        """Test that _protect_files makes critical files read-only"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a test file
            test_file = tmpdir / "manage.py"
            test_file.write_text("test content")
            
            service = CodexService(project_dir=str(tmpdir))
            service._protect_files(tmpdir)
            
            # Check if file is read-only (user has read permission but not write)
            mode = os.stat(test_file).st_mode
            # File should not have write permission
            self.assertFalse(mode & 0o200)  # User write bit should be off
    
    def test_unprotect_files_restores_write_permission(self):
        """Test that _unprotect_files restores write permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create and protect a test file
            test_file = tmpdir / "manage.py"
            test_file.write_text("test content")
            
            service = CodexService(project_dir=str(tmpdir))
            service._protect_files(tmpdir)
            service._unprotect_files(tmpdir)
            
            # Check if file has write permission restored
            mode = os.stat(test_file).st_mode
            self.assertTrue(mode & 0o200)  # User write bit should be on


class TestCodexServiceImplement(TestCase):
    """Test the main implement() method"""
    
    @patch.object(CodexService, '_run_codex')
    @patch.object(CodexService, '_snapshot_files')
    @patch.object(CodexService, '_detect_changes')
    @patch.object(CodexService, '_protect_files')
    @patch.object(CodexService, '_unprotect_files')
    def test_implement_falls_back_on_failure(
        self, mock_unprotect, mock_protect, mock_detect, mock_snapshot, mock_run
    ):
        """Test that implement() returns error result on Codex failure"""
        mock_snapshot.return_value = {}
        mock_run.return_value = {
            'success': False,
            'events': [],
            'error': 'Codex execution failed'
        }
        
        service = CodexService()
        result = service.implement(
            feature_description="Add feature",
            implementation_plan=json.dumps({"plan": ["Step 1"]}),
            files_to_modify=["test.py"]
        )
        
        self.assertFalse(result['success'])
        self.assertIn('failed', result['error'])
        # Verify unprotect was called even on failure
        mock_unprotect.assert_called_once()
    
    @patch.object(CodexService, '_run_codex')
    @patch.object(CodexService, '_snapshot_files')
    @patch.object(CodexService, '_detect_changes')
    @patch.object(CodexService, '_extract_summary')
    @patch.object(CodexService, '_extract_token_usage')
    @patch.object(CodexService, '_protect_files')
    @patch.object(CodexService, '_unprotect_files')
    def test_implement_returns_success_with_changes(
        self, mock_unprotect, mock_protect, mock_usage, mock_summary,
        mock_detect, mock_snapshot, mock_run
    ):
        """Test that implement() returns success when Codex makes changes"""
        mock_snapshot.return_value = {'test.py': 'original'}
        mock_run.return_value = {
            'success': True,
            'events': [{'type': 'test_event'}],
            'error': None
        }
        mock_detect.return_value = [
            {
                'file': 'test.py',
                'code': 'modified content',
                'changes': ['Added feature'],
                'notes': ''
            }
        ]
        mock_summary.return_value = 'Feature implemented successfully'
        mock_usage.return_value = {'input_tokens': 1000, 'output_tokens': 500, 'cached_input_tokens': 0}
        
        service = CodexService()
        result = service.implement(
            feature_description="Add feature",
            implementation_plan=json.dumps({"plan": ["Step 1"]}),
            files_to_modify=["test.py"]
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['files_changed']), 1)
        self.assertEqual(result['files_changed'][0]['file'], 'test.py')
        self.assertEqual(result['summary'], 'Feature implemented successfully')
        self.assertEqual(result['token_usage']['input_tokens'], 1000)
        # Verify unprotect was called
        mock_unprotect.assert_called_once()


if __name__ == '__main__':
    unittest.main()
