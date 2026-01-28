"""
Test Fixer Service for Phase 5: AI-Powered Test Fixing

This service uses AI to analyze test failures and generate fixes:
- Analyzes test failure output
- Examines the code that's failing
- Generates fixes using OpenAI
- Returns modified code
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from django.conf import settings


class TestFixer:
    """Handles AI-powered test failure analysis and fixing"""
    
    def __init__(self, ai_service):
        """
        Initialize with AI service.
        
        Args:
            ai_service: Instance of AIService for making OpenAI calls
        """
        self.ai_service = ai_service
        self.base_path = Path(settings.BASE_DIR)
    
    def analyze_test_failure(self, test_result: Dict[str, Any], feature_description: str) -> Dict[str, Any]:
        """
        Analyze test failure and determine what needs to be fixed.
        
        Args:
            test_result: Result dictionary from TestRunner
            feature_description: Description of the feature that was implemented
            
        Returns:
            Dictionary with:
            {
                'analysis': str,  # AI's analysis of the problem
                'suggested_fixes': List[str],  # List of suggested fixes
                'files_to_fix': List[str]  # Files that likely need fixing
            }
        """
        if not self.ai_service.is_enabled():
            return {
                'analysis': 'AI service not enabled. Cannot analyze test failures.',
                'suggested_fixes': [],
                'files_to_fix': []
            }
        
        # Build prompt for AI
        prompt = f"""Analyze the following test failure for a Django web application feature implementation.

Feature Implemented: {feature_description}

Test Framework: {test_result.get('test_framework', 'unknown')}
Tests Run: {test_result.get('total_tests', 0)}
Tests Passed: {test_result.get('passed_tests', 0)}
Tests Failed: {test_result.get('failed_tests', 0)}

Test Output:
{test_result.get('stdout', '')[:2000]}

Error Details:
{test_result.get('error_details', '')[:1000]}

Please analyze this test failure and provide:
1. A brief explanation of what went wrong
2. Which files likely need to be fixed
3. Specific suggestions for fixing the issues

Respond in JSON format:
{{
    "analysis": "brief explanation",
    "files_to_fix": ["file1.py", "file2.py"],
    "suggested_fixes": ["fix 1", "fix 2"]
}}"""
        
        try:
            response = self.ai_service.chat(prompt)
            
            # Try to parse JSON response
            import json
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    analysis_data = json.loads(json_str)
                    return analysis_data
            except json.JSONDecodeError:
                pass
            
            # Fallback: return raw response
            return {
                'analysis': response,
                'suggested_fixes': [],
                'files_to_fix': []
            }
            
        except Exception as e:
            return {
                'analysis': f'Error analyzing test failure: {str(e)}',
                'suggested_fixes': [],
                'files_to_fix': []
            }
    
    def generate_fix(self, 
                     file_path: str, 
                     test_result: Dict[str, Any], 
                     feature_description: str,
                     analysis: Dict[str, Any]) -> Optional[str]:
        """
        Generate fixed code for a specific file.
        
        Args:
            file_path: Path to the file that needs fixing
            test_result: Test result dictionary
            feature_description: Description of the feature
            analysis: Analysis from analyze_test_failure
            
        Returns:
            Fixed code as string, or None if generation fails
        """
        if not self.ai_service.is_enabled():
            return None
        
        # Read current file content
        full_path = self.base_path / file_path
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                current_code = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
        
        # Build prompt for AI
        prompt = f"""Fix the following code to make tests pass.

Feature Being Implemented: {feature_description}

File to Fix: {file_path}

Current Code:
```
{current_code}
```

Test Failure Analysis:
{analysis.get('analysis', 'No analysis available')}

Test Error Details:
{test_result.get('error_details', '')[:1000]}

Suggested Fixes:
{chr(10).join(f'- {fix}' for fix in analysis.get('suggested_fixes', []))}

Please generate the COMPLETE fixed code for {file_path}.
Make only the necessary changes to fix the test failures.
Preserve all existing functionality that isn't broken.

Respond with ONLY the complete fixed code, no explanations, no markdown code blocks.
Just the raw Python/HTML/JavaScript/CSS code that should replace the current file content."""
        
        try:
            response = self.ai_service.chat(prompt)
            
            # Clean up response (remove markdown code blocks if present)
            if '```' in response:
                # Extract code from markdown blocks
                lines = response.split('\n')
                code_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                
                if code_lines:
                    return '\n'.join(code_lines)
            
            return response
            
        except Exception as e:
            print(f"Error generating fix: {e}")
            return None
    
    def apply_fix(self, file_path: str, fixed_code: str) -> bool:
        """
        Apply the fixed code to a file.
        
        Args:
            file_path: Path to the file
            fixed_code: The fixed code to write
            
        Returns:
            True if successful, False otherwise
        """
        full_path = self.base_path / file_path
        
        try:
            # Create backup before modifying
            if full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + '.backup-fix')
                with open(full_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as backup:
                        backup.write(f.read())
            
            # Write fixed code
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            print(f"✅ Applied fix to {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply fix to {file_path}: {e}")
            return False
