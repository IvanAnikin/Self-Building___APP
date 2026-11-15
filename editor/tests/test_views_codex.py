"""
Unit tests for views.py changes related to Codex integration

Tests that implement_feature correctly:
- Uses Codex when available
- Falls back to legacy when Codex unavailable
- Falls back on Codex error
- Includes engine field in response
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from editor.models import FeatureRequest
import json


class TestImplementFeatureCodexIntegration(TestCase):
    """Test implement_feature view with Codex integration"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('editor.views.codex_service')
    @patch('editor.views.feature_implementer')
    def test_implement_feature_uses_codex_when_available(
        self, mock_implementer, mock_codex
    ):
        """Test that implement_feature uses Codex when available"""
        # Create a feature with analysis
        feature = FeatureRequest.objects.create(
            user=self.user,
            description="Add dark mode toggle",
            status='approved',
            implementation_plan=json.dumps({
                "feasible": True,
                "plan": ["Add button", "Add CSS"],
                "files_to_modify": ["static/css/style.css"]
            })
        )
        
        # Mock Codex as available and successful
        mock_codex.is_available.return_value = True
        mock_codex._snapshot_files.return_value = {
            'static/css/style.css': 'original css'
        }
        mock_codex.implement.return_value = {
            'success': True,
            'files_changed': [{
                'file': 'static/css/style.css',
                'code': 'modified css',
                'changes': ['Added dark mode'],
                'notes': ''
            }],
            'summary': 'Added dark mode successfully',
            'events': [],
            'token_usage': {'input_tokens': 1000, 'output_tokens': 500, 'cached_input_tokens': 0},
            'error': None
        }
        mock_codex.project_dir = MagicMock()
        
        # Make request
        response = self.client.post(
            '/api/features/implement/',
            data=json.dumps({'feature_id': feature.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify Codex was called
        mock_codex.implement.assert_called_once()
        
        # Verify response includes engine field
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['engine'], 'codex')
        self.assertEqual(len(data['generated_files']), 1)
        
        # Verify feature was updated
        feature.refresh_from_db()
        self.assertEqual(feature.implementation_engine, 'codex')
    
    @patch('editor.views.codex_service')
    @patch('editor.views.feature_implementer')
    def test_implement_feature_falls_back_when_codex_unavailable(
        self, mock_implementer, mock_codex
    ):
        """Test that implement_feature falls back to legacy when Codex unavailable"""
        # Create a feature with analysis
        feature = FeatureRequest.objects.create(
            user=self.user,
            description="Add feature",
            status='approved',
            implementation_plan=json.dumps({
                "feasible": True,
                "plan": ["Step 1"],
                "files_to_modify": ["test.py"]
            })
        )
        
        # Mock Codex as unavailable
        mock_codex.is_available.return_value = False
        
        # Mock legacy implementer
        mock_implementer.read_file_safely.return_value = {
            'exists': False,
            'content': None
        }
        mock_implementer.generate_code.return_value = {
            'success': True,
            'code': 'generated code',
            'changes_made': ['Added feature'],
            'notes': ''
        }
        
        # Make request
        response = self.client.post(
            '/api/features/implement/',
            data=json.dumps({'feature_id': feature.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify legacy implementer was called
        mock_implementer.generate_code.assert_called_once()
        
        # Verify response indicates legacy engine
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['engine'], 'legacy')
        
        # Verify feature was updated with legacy engine
        feature.refresh_from_db()
        self.assertEqual(feature.implementation_engine, 'legacy')
    
    @patch('editor.views.codex_service')
    @patch('editor.views.feature_implementer')
    def test_implement_feature_falls_back_on_codex_error(
        self, mock_implementer, mock_codex
    ):
        """Test that implement_feature falls back to legacy on Codex error"""
        # Create a feature with analysis
        feature = FeatureRequest.objects.create(
            user=self.user,
            description="Add feature",
            status='approved',
            implementation_plan=json.dumps({
                "feasible": True,
                "plan": ["Step 1"],
                "files_to_modify": ["test.py"]
            })
        )
        
        # Mock Codex as available but failing
        mock_codex.is_available.return_value = True
        mock_codex._snapshot_files.return_value = {'test.py': 'original'}
        mock_codex.implement.return_value = {
            'success': False,
            'files_changed': [],
            'summary': '',
            'events': [],
            'token_usage': {},
            'error': 'Codex execution failed'
        }
        mock_codex.project_dir = MagicMock()
        
        # Mock legacy implementer as fallback
        mock_implementer.read_file_safely.return_value = {
            'exists': False,
            'content': None
        }
        mock_implementer.generate_code.return_value = {
            'success': True,
            'code': 'generated code',
            'changes_made': ['Added feature'],
            'notes': ''
        }
        
        # Make request
        response = self.client.post(
            '/api/features/implement/',
            data=json.dumps({'feature_id': feature.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify fallback to legacy was triggered
        mock_implementer.generate_code.assert_called_once()
        
        # Verify response indicates legacy engine (fallback)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['engine'], 'legacy')
    
    @patch('editor.views.codex_service')
    def test_implement_feature_response_includes_engine_field(self, mock_codex):
        """Test that implement_feature response always includes engine field"""
        # Create a feature with analysis
        feature = FeatureRequest.objects.create(
            user=self.user,
            description="Add feature",
            status='approved',
            implementation_plan=json.dumps({
                "feasible": True,
                "plan": ["Step 1"],
                "files_to_modify": ["test.py"]
            })
        )
        
        # Mock Codex as unavailable to use legacy
        mock_codex.is_available.return_value = False
        
        # Make request
        response = self.client.post(
            '/api/features/implement/',
            data=json.dumps({'feature_id': feature.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify engine field exists in response
        self.assertIn('engine', data)
        self.assertIn(data['engine'], ['codex', 'legacy'])


class TestFeatureRequestModel(TestCase):
    """Test FeatureRequest model changes"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_feature_request_has_implementation_engine_field(self):
        """Test that FeatureRequest has implementation_engine field"""
        feature = FeatureRequest.objects.create(
            user=self.user,
            description="Test feature"
        )
        
        # Field should exist with default value
        self.assertTrue(hasattr(feature, 'implementation_engine'))
        self.assertEqual(feature.implementation_engine, 'legacy')
    
    def test_feature_request_engine_choices(self):
        """Test that FeatureRequest accepts valid engine choices"""
        # Test 'legacy' choice
        feature1 = FeatureRequest.objects.create(
            user=self.user,
            description="Test feature 1",
            implementation_engine='legacy'
        )
        self.assertEqual(feature1.implementation_engine, 'legacy')
        
        # Test 'codex' choice
        feature2 = FeatureRequest.objects.create(
            user=self.user,
            description="Test feature 2",
            implementation_engine='codex'
        )
        self.assertEqual(feature2.implementation_engine, 'codex')


if __name__ == '__main__':
    import unittest
    unittest.main()
