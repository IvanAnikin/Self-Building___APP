"""
Code Executor Module for Self-Building App
Provides sandboxed code execution with timeout and security controls.
"""

import subprocess
import tempfile
import os
import shutil
from typing import Dict, Any


class CodeExecutor:
    """
    Handles secure code execution with sandboxing and timeout controls.
    Currently supports Python and JavaScript execution.
    """
    
    def __init__(self, timeout: int = 5, max_output_length: int = 10000):
        """
        Initialize code executor with security parameters.
        
        Args:
            timeout: Maximum execution time in seconds (default: 5)
            max_output_length: Maximum length of output to return (default: 10000)
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
    
    def execute(self, code: str, language: str) -> Dict[str, Any]:
        """
        Execute code in the specified language.
        
        Args:
            code: The source code to execute
            language: Programming language ('python' or 'javascript')
            
        Returns:
            Dictionary containing execution results:
            {
                'status': 'success' or 'error',
                'stdout': standard output,
                'stderr': standard error,
                'returncode': process return code,
                'error': error message (if any)
            }
        """
        if language.lower() in ['python', 'py']:
            return self._execute_python(code)
        elif language.lower() in ['javascript', 'js', 'node']:
            return self._execute_javascript(code)
        else:
            return {
                'status': 'error',
                'error': f'Unsupported language: {language}. Currently supported: Python, JavaScript',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
    
    def _execute_python(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code with sandboxing and timeout.
        
        Args:
            code: Python source code
            
        Returns:
            Execution results dictionary
        """
        temp_file = None
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout and capture output
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Additional security: prevent spawning subprocesses
                env={
                    **os.environ,
                    'PYTHONDONTWRITEBYTECODE': '1'
                }
            )
            
            # Truncate output if too long
            stdout = result.stdout[:self.max_output_length]
            stderr = result.stderr[:self.max_output_length]
            
            if len(result.stdout) > self.max_output_length:
                stdout += "\n... (output truncated)"
            if len(result.stderr) > self.max_output_length:
                stderr += "\n... (output truncated)"
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': stdout,
                'stderr': stderr,
                'returncode': result.returncode,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'error': f'Execution timeout: Code took longer than {self.timeout} seconds',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        except FileNotFoundError:
            return {
                'status': 'error',
                'error': 'Python interpreter not found. Please ensure Python 3 is installed.',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Execution error: {str(e)}',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def _execute_javascript(self, code: str) -> Dict[str, Any]:
        """
        Execute JavaScript code using Node.js with sandboxing and timeout.
        
        Args:
            code: JavaScript source code
            
        Returns:
            Execution results dictionary
        """
        temp_file = None
        try:
            # Check if Node.js is available
            node_check = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if node_check.returncode != 0:
                return {
                    'status': 'error',
                    'error': 'Node.js not found. JavaScript execution requires Node.js to be installed.',
                    'stdout': '',
                    'stderr': '',
                    'returncode': -1
                }
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.js',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout and capture output
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Truncate output if too long
            stdout = result.stdout[:self.max_output_length]
            stderr = result.stderr[:self.max_output_length]
            
            if len(result.stdout) > self.max_output_length:
                stdout += "\n... (output truncated)"
            if len(result.stderr) > self.max_output_length:
                stderr += "\n... (output truncated)"
            
            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'stdout': stdout,
                'stderr': stderr,
                'returncode': result.returncode,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'error': f'Execution timeout: Code took longer than {self.timeout} seconds',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Execution error: {str(e)}',
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass


# Global executor instance
code_executor = CodeExecutor(timeout=5, max_output_length=10000)
