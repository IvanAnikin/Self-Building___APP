from django.test import TestCase, Client
from django.urls import reverse
from .models import CodeExecution
import json


class CodeExecutionTests(TestCase):
    """Tests for code execution functionality"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.execute_url = reverse('execute_code')
    
    def test_execute_python_hello_world(self):
        """Test basic Python code execution"""
        code = """
print("Hello, World!")
"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'python',
                'filename': 'test.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Hello, World!', data['stdout'])
        self.assertEqual(data['returncode'], 0)
    
    def test_execute_python_with_calculation(self):
        """Test Python code with calculations"""
        code = """
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'python',
                'filename': 'calc.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('2 + 2 = 4', data['stdout'])
    
    def test_execute_python_syntax_error(self):
        """Test Python code with syntax error"""
        code = """
print("missing closing quote)
"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'python',
                'filename': 'error.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('SyntaxError', data['stderr'] or '')
        self.assertNotEqual(data['returncode'], 0)
    
    def test_execute_python_runtime_error(self):
        """Test Python code with runtime error"""
        code = """
x = 10 / 0
"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'python',
                'filename': 'error.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('ZeroDivisionError', data['stderr'])
    
    def test_execute_empty_code(self):
        """Test execution with empty code"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': '',
                'language': 'python',
                'filename': 'empty.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_execute_saves_to_database(self):
        """Test that execution is saved to database"""
        initial_count = CodeExecution.objects.count()
        
        code = 'print("Test")'
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'python',
                'filename': 'test.py'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CodeExecution.objects.count(), initial_count + 1)
        
        execution = CodeExecution.objects.latest('executed_at')
        self.assertEqual(execution.code, code)
        self.assertEqual(execution.language, 'python')
        self.assertEqual(execution.filename, 'test.py')
        self.assertEqual(execution.status, 'success')
    
    def test_execute_unsupported_language(self):
        """Test execution with unsupported language"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': 'println("Hello")',
                'language': 'rust',
                'filename': 'test.rs'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('Unsupported language', data['error'])
    
    def test_execute_javascript_hello_world(self):
        """Test basic JavaScript code execution (if Node.js is available)"""
        code = """
console.log("Hello from JavaScript!");
"""
        response = self.client.post(
            self.execute_url,
            data=json.dumps({
                'code': code,
                'language': 'javascript',
                'filename': 'test.js'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Either succeeds with Node.js or fails gracefully
        if data['status'] == 'success':
            self.assertIn('Hello from JavaScript!', data['stdout'])
        else:
            # Node.js not installed - acceptable
            self.assertIn('Node.js', data['error'])
    
    def test_execute_method_not_allowed(self):
        """Test that GET requests are not allowed"""
        response = self.client.get(self.execute_url)
        self.assertEqual(response.status_code, 405)


class CodeExecutorUnitTests(TestCase):
    """Unit tests for CodeExecutor class"""
    
    def test_executor_timeout(self):
        """Test that long-running code times out"""
        from .code_executor import CodeExecutor
        
        executor = CodeExecutor(timeout=1)
        code = """
import time
time.sleep(5)
print("Should not reach here")
"""
        result = executor.execute(code, 'python')
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('timeout', result['error'].lower())
    
    def test_executor_output_truncation(self):
        """Test that long output is truncated"""
        from .code_executor import CodeExecutor
        
        executor = CodeExecutor(max_output_length=100)
        code = """
for i in range(1000):
    print(f"Line {i}: This is a very long line with lots of text")
"""
        result = executor.execute(code, 'python')
        
        # Output should be truncated
        self.assertLessEqual(len(result['stdout']), 130)  # Buffer for truncation message
        self.assertIn('truncated', result['stdout'].lower())

