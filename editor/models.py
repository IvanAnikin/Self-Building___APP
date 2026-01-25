from django.db import models

class ChatMessage(models.Model):
    """Store chat messages between user and bot"""
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
    test_results = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feature Request: {self.description[:50]}"

class CodeExecution(models.Model):
    """Store code execution history and results"""
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

