from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    """Store chat messages between user and bot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Phase 5: Multi-user support
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_user = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Message at {self.timestamp}"

class CodeSnippet(models.Model):
    """Store code snippets from the editor"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Phase 5: Multi-user support
    filename = models.CharField(max_length=255, default='untitled.txt')
    code = models.TextField()
    language = models.CharField(max_length=50, default='python')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.filename

class FeatureRequest(models.Model):
    """Store feature requests from users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Phase 5: Multi-user support
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Phase 4: Self-modification fields
    generated_code = models.TextField(blank=True, default='')
    implementation_plan = models.TextField(blank=True, default='')
    files_modified = models.JSONField(default=list, blank=True)
    git_commit_hash = models.CharField(max_length=40, blank=True, default='')
    error_log = models.TextField(blank=True, default='')
    test_results_summary = models.TextField(blank=True, default='')  # Renamed to avoid conflict
    
    # Phase 5: Testing fields
    tests_passed = models.BooleanField(default=False)
    test_iterations = models.IntegerField(default=0)
    last_test_result = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feature Request: {self.description[:50]}"

class CodeExecution(models.Model):
    """Store code execution history and results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Phase 5: Multi-user support
    code = models.TextField()
    language = models.CharField(max_length=50, default='python')
    filename = models.CharField(max_length=255, default='untitled.txt')
    stdout = models.TextField(blank=True, default='')
    stderr = models.TextField(blank=True, default='')
    returncode = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
    ], default='success')
    error_message = models.TextField(blank=True, default='')
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"Execution of {self.filename} at {self.executed_at}"


# Phase 5: New Models for Multi-User, Version Control, and Testing

class UserProfile(models.Model):
    """Extended user profile with workspace settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    git_branch_name = models.CharField(max_length=100)  # e.g., "user-1-workspace"
    workspace_path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    # Settings
    theme = models.CharField(max_length=20, default='dark')
    editor_font_size = models.IntegerField(default=14)
    auto_save = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class FeatureVersion(models.Model):
    """Track version history of feature implementations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature = models.ForeignKey(FeatureRequest, on_delete=models.CASCADE, related_name='versions')
    commit_hash = models.CharField(max_length=40)
    commit_message = models.CharField(max_length=255)
    files_changed = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot of code at this version
    code_snapshot = models.JSONField(default=dict)  # {file_path: content}
    
    # Status at this version
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('reverted', 'Reverted'),
    ], default='active')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Version {self.commit_hash[:7]} by {self.user.username}"


class TestResult(models.Model):
    """Store results of automated testing"""
    feature = models.ForeignKey(FeatureRequest, on_delete=models.CASCADE, related_name='test_results')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.ForeignKey(FeatureVersion, on_delete=models.CASCADE, null=True, blank=True)
    
    # Test execution details
    test_command = models.CharField(max_length=255)  # e.g., "pytest tests/"
    test_framework = models.CharField(max_length=50, default='pytest')  # pytest, unittest, django
    
    # Results
    passed = models.BooleanField(default=False)
    total_tests = models.IntegerField(default=0)
    passed_tests = models.IntegerField(default=0)
    failed_tests = models.IntegerField(default=0)
    
    # Output
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    error_details = models.TextField(blank=True)
    
    # Retry tracking
    iteration = models.IntegerField(default=1)  # Which attempt (1-3)
    
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        status = "PASSED" if self.passed else "FAILED"
        return f"Test {status}: {self.feature.description[:30]} (Iteration {self.iteration})"

