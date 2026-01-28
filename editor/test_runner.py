"""
Test Runner Service for Phase 5: Automated Testing

This service handles automated testing of feature implementations:
- Detects test framework (pytest, unittest, Django tests)
- Runs tests and parses results
- Returns structured test results
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from django.conf import settings


class TestRunner:
    """Handles automated test execution"""
    
    def __init__(self, user):
        self.user = user
        self.workspace_path = Path(settings.BASE_DIR)
    
    def detect_test_framework(self) -> str:
        """
        Detect which test framework is being used.
        
        Returns:
            'pytest', 'unittest', 'django', or 'none'
        """
        # Check for pytest
        if (self.workspace_path / 'pytest.ini').exists() or \
           (self.workspace_path / 'pyproject.toml').exists():
            # Check if pytest is installed
            try:
                subprocess.run(['pytest', '--version'], capture_output=True, timeout=5)
                return 'pytest'
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Check for Django tests
        if (self.workspace_path / 'manage.py').exists():
            # Look for test files in apps
            test_files = list(self.workspace_path.glob('*/tests.py'))
            test_dirs = list(self.workspace_path.glob('*/tests/'))
            if test_files or test_dirs:
                return 'django'
        
        # Check for unittest
        test_files = list(self.workspace_path.glob('test_*.py'))
        if test_files:
            return 'unittest'
        
        return 'none'
    
    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute tests and return results.
        
        Args:
            test_path: Optional specific test path to run
            
        Returns:
            Dictionary with:
            {
                'passed': bool,
                'total_tests': int,
                'passed_tests': int,
                'failed_tests': int,
                'stdout': str,
                'stderr': str,
                'error_details': str,
                'test_framework': str
            }
        """
        framework = self.detect_test_framework()
        
        if framework == 'none':
            return {
                'passed': True,  # No tests = considered passing
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': 'No tests found',
                'stderr': '',
                'error_details': '',
                'test_framework': 'none'
            }
        
        if framework == 'pytest':
            return self._run_pytest(test_path)
        elif framework == 'django':
            return self._run_django_tests(test_path)
        elif framework == 'unittest':
            return self._run_unittest(test_path)
        
        return self._no_tests_result()
    
    def _run_pytest(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """Run pytest and parse results"""
        command = ['pytest', '-v', '--tb=short']
        if test_path:
            command.append(test_path)
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            # Parse pytest output
            passed_tests = len(re.findall(r'PASSED', stdout))
            failed_tests = len(re.findall(r'FAILED', stdout))
            total_tests = passed_tests + failed_tests
            
            # Extract error details
            error_details = self._extract_pytest_errors(stdout)
            
            return {
                'passed': result.returncode == 0,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'stdout': stdout,
                'stderr': stderr,
                'error_details': error_details,
                'test_framework': 'pytest'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': 'Test execution timed out after 60 seconds',
                'error_details': 'Timeout',
                'test_framework': 'pytest'
            }
        except Exception as e:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': str(e),
                'error_details': str(e),
                'test_framework': 'pytest'
            }
    
    def _run_django_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """Run Django tests and parse results"""
        command = ['python', 'manage.py', 'test', '--verbosity=2']
        if test_path:
            command.append(test_path)
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            # Parse Django test output
            # Look for lines like "Ran X tests in Y seconds"
            ran_match = re.search(r'Ran (\d+) test', stdout)
            total_tests = int(ran_match.group(1)) if ran_match else 0
            
            # Check for failures
            failed_match = re.search(r'FAILED \(.*?failures=(\d+)', stdout)
            failed_tests = int(failed_match.group(1)) if failed_match else 0
            
            error_match = re.search(r'errors=(\d+)', stdout)
            error_tests = int(error_match.group(1)) if error_match else 0
            
            failed_tests += error_tests
            passed_tests = total_tests - failed_tests
            
            # Extract error details
            error_details = self._extract_django_errors(stdout, stderr)
            
            return {
                'passed': result.returncode == 0,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'stdout': stdout,
                'stderr': stderr,
                'error_details': error_details,
                'test_framework': 'django'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': 'Test execution timed out after 60 seconds',
                'error_details': 'Timeout',
                'test_framework': 'django'
            }
        except Exception as e:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': str(e),
                'error_details': str(e),
                'test_framework': 'django'
            }
    
    def _run_unittest(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """Run unittest and parse results"""
        command = ['python', '-m', 'unittest', 'discover', '-v']
        if test_path:
            command = ['python', '-m', 'unittest', test_path, '-v']
        
        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            # Parse unittest output
            ran_match = re.search(r'Ran (\d+) test', stderr)
            total_tests = int(ran_match.group(1)) if ran_match else 0
            
            # Check for failures
            if 'FAILED' in stderr:
                failed_match = re.search(r'failures=(\d+)', stderr)
                failed_tests = int(failed_match.group(1)) if failed_match else 0
                error_match = re.search(r'errors=(\d+)', stderr)
                error_tests = int(error_match.group(1)) if error_match else 0
                failed_tests += error_tests
            else:
                failed_tests = 0
            
            passed_tests = total_tests - failed_tests
            
            # Extract error details
            error_details = self._extract_unittest_errors(stderr)
            
            return {
                'passed': result.returncode == 0,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'stdout': stdout,
                'stderr': stderr,
                'error_details': error_details,
                'test_framework': 'unittest'
            }
            
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': 'Test execution timed out after 60 seconds',
                'error_details': 'Timeout',
                'test_framework': 'unittest'
            }
        except Exception as e:
            return {
                'passed': False,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'stdout': '',
                'stderr': str(e),
                'error_details': str(e),
                'test_framework': 'unittest'
            }
    
    def _extract_pytest_errors(self, output: str) -> str:
        """Extract error details from pytest output"""
        errors = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if 'FAILED' in line:
                # Get the failed test name
                errors.append(line)
                # Look for assertion error in next few lines
                for j in range(i + 1, min(i + 10, len(lines))):
                    if 'AssertionError' in lines[j] or 'Error' in lines[j]:
                        errors.append(lines[j])
                        break
        
        return '\n'.join(errors) if errors else 'No specific error details'
    
    def _extract_django_errors(self, stdout: str, stderr: str) -> str:
        """Extract error details from Django test output"""
        # Look for FAIL or ERROR sections
        errors = []
        output = stdout + '\n' + stderr
        lines = output.split('\n')
        
        in_error_section = False
        for line in lines:
            if line.startswith('FAIL:') or line.startswith('ERROR:'):
                in_error_section = True
                errors.append(line)
            elif in_error_section:
                if line.startswith('------'):
                    in_error_section = False
                else:
                    errors.append(line)
        
        return '\n'.join(errors[:50]) if errors else 'No specific error details'  # Limit to first 50 lines
    
    def _extract_unittest_errors(self, stderr: str) -> str:
        """Extract error details from unittest output"""
        # Look for FAIL or ERROR sections
        errors = []
        lines = stderr.split('\n')
        
        in_error_section = False
        for line in lines:
            if line.startswith('FAIL:') or line.startswith('ERROR:'):
                in_error_section = True
                errors.append(line)
            elif in_error_section:
                if line.startswith('------'):
                    in_error_section = False
                else:
                    errors.append(line)
        
        return '\n'.join(errors[:50]) if errors else 'No specific error details'
    
    def _no_tests_result(self) -> Dict[str, Any]:
        """Return a default result when no tests are found"""
        return {
            'passed': True,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'stdout': 'No tests found',
            'stderr': '',
            'error_details': '',
            'test_framework': 'none'
        }
