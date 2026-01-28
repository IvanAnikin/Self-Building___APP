# Phase 5 Implementation Plan: Multi-User, Version Control & Automated Testing

**Status:** 📋 Planning  
**Priority:** HIGH  
**Estimated Time:** 8-12 hours  
**Complexity:** High

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements Summary](#requirements-summary)
3. [Architecture Design](#architecture-design)
4. [Database Schema](#database-schema)
5. [Implementation Steps](#implementation-steps)
6. [API Endpoints](#api-endpoints)
7. [Frontend Changes](#frontend-changes)
8. [Testing Strategy](#testing-strategy)
9. [Security Considerations](#security-considerations)
10. [Migration Plan](#migration-plan)

---

## Overview

Phase 5 transforms the Self-Building App from a single-user application into a multi-user platform with version control and automated testing. Each user will have:

- **Isolated Environment:** Own files, chat history, and feature requests
- **Version Control:** Git-based version tracking with branch management
- **Automated Testing:** AI-powered testing and rollback mechanism

### Current State (Phases 1-4)

✅ **Completed Features:**
- Dark mode code editor with AI chatbot
- Feature request detection and tracking
- AI-powered context-aware code generation
- User approval workflow with diff viewer
- Automatic file backups
- Code execution (Python/JavaScript)

❌ **Missing Features (Phase 5):**
- User authentication and authorization
- Multi-user support with data isolation
- Git version control integration
- Automated testing framework
- Rollback mechanism

---

## Requirements Summary

### 1. User Authentication & Multi-User Support

**Requirements:**
- User registration and login system
- Each user has isolated workspace
- User-specific:
  - Code snippets (files they can edit)
  - Chat history
  - Feature requests
  - Version history
- One user cannot modify another user's application
- Each user builds their own version of the app

**Key Points:**
- Use Django's built-in authentication system
- Add User foreign keys to all models
- Filter all queries by current user
- Session-based authentication

### 2. Version Control Integration

**Requirements:**
- Git integration for tracking changes
- Each user has their own branch: `user-{user_id}-workspace`
- Per-feature commits when changes are applied
- Version roadmap UI showing commit history
- Click-to-navigate to any previous version
- Branch switching functionality

**Key Points:**
- Use GitPython or subprocess for git commands
- Commit format: `"feat: {feature_description} [user-{user_id}]"`
- Store commit hashes in FeatureRequest model
- Create visual timeline in UI

### 3. Automated Testing & Rollback

**Requirements:**
- After feature implementation, run tests automatically
- Test workflow:
  1. Apply feature changes
  2. Run existing tests
  3. If tests fail → Send logs + code to AI
  4. AI attempts to fix (max 3 iterations)
  5. If still failing → Rollback changes + notify user
  6. If tests pass → User can preview and keep changes
- Rollback mechanism reverts to last working commit
- User notification of test results

**Key Points:**
- Detect test files in project
- Support pytest, unittest, Django tests
- Limited retry iterations (max 3)
- Git-based rollback (hard reset to previous commit)
- Store test results in database

---

## Architecture Design

### System Architecture (Phase 5)

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
├──────────────────────┬──────────────────────────────────┤
│   Code Editor        │       AI Chatbot Interface       │
│   (User Workspace)   │    (User-specific history)       │
└──────────────────────┴──────────────────────────────────┘
            │                          │
            │     Authenticated        │
            ├────── HTTP/AJAX ─────────┤
            │     (Session Token)      │
            ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│         Django Backend (Multi-User Support)              │
├─────────────────────────────────────────────────────────┤
│  Authentication Middleware → User Context                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  Views   │  │ Git Srv  │  │  Test Runner         │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     ORM Layer (User-Filtered)            │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite Database (db.sqlite3)                │
├─────────────────────────────────────────────────────────┤
│  User | ChatMessage | CodeSnippet | FeatureRequest      │
│  UserBranch | FeatureVersion | TestResult               │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│          Git Repository (Per-User Branches)              │
├─────────────────────────────────────────────────────────┤
│  main (protected)                                        │
│  user-1-workspace (User 1's code)                        │
│  user-2-workspace (User 2's code)                        │
│  user-3-workspace (User 3's code)                        │
└─────────────────────────────────────────────────────────┘
```

### Data Flow: Feature Implementation with Testing

```
User Request Feature
    ↓
AI Analyzes & Generates Code
    ↓
User Reviews & Approves
    ↓
┌─────────────────────────────┐
│   Apply Changes to Files    │
│   (User's workspace files)  │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│   Git Commit                │
│   (user-X-workspace branch) │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│   Run Automated Tests       │
│   (pytest/unittest)         │
└─────────────────────────────┘
    ↓
    ├─── Tests PASS ─────────────────┐
    │                                 ↓
    │                        User Notified (Success)
    │                        Feature Status: completed
    │
    └─── Tests FAIL ─────────────────┐
                                     ↓
                             ┌───────────────────┐
                             │ Send Logs to AI   │
                             │ Request Fix       │
                             └───────────────────┘
                                     ↓
                             ┌───────────────────┐
                             │ AI Generates Fix  │
                             └───────────────────┘
                                     ↓
                             ┌───────────────────┐
                             │ Apply Fix         │
                             │ Commit Changes    │
                             │ Re-run Tests      │
                             └───────────────────┘
                                     ↓
                             Iteration < 3?
                                 ↓       ↓
                               Yes      No
                                 ↓       ↓
                           (Repeat)  ┌─────────────────┐
                                     │ Git Rollback    │
                                     │ to Last Commit  │
                                     └─────────────────┘
                                            ↓
                                     User Notified (Failed)
                                     Feature Status: failed
```

---

## Database Schema

### New Models

#### 1. UserProfile (extends Django User)

```python
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
```

#### 2. FeatureVersion (Version History)

```python
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
```

#### 3. TestResult (Automated Testing)

```python
class TestResult(models.Model):
    """Store results of automated testing"""
    feature = models.ForeignKey(FeatureRequest, on_delete=models.CASCADE, related_name='test_results')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.ForeignKey(FeatureVersion, on_delete=models.CASCADE, null=True)
    
    # Test execution details
    test_command = models.CharField(max_length=255)  # e.g., "pytest tests/"
    test_framework = models.CharField(max_length=50)  # pytest, unittest, django
    
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
```

### Updated Models

#### ChatMessage (Add User FK)

```python
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # NEW
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_user = models.BooleanField(default=True)
```

#### CodeSnippet (Add User FK)

```python
class CodeSnippet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # NEW
    filename = models.CharField(max_length=255, default='untitled.txt')
    code = models.TextField()
    language = models.CharField(max_length=50, default='python')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### FeatureRequest (Add User FK)

```python
class FeatureRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # NEW
    description = models.TextField()
    status = models.CharField(max_length=20, ...)
    # ... existing fields ...
    
    # Testing fields (NEW)
    tests_passed = models.BooleanField(default=False)
    test_iterations = models.IntegerField(default=0)
    last_test_result = models.TextField(blank=True)
```

---

## Implementation Steps

### Part 1: User Authentication (2-3 hours)

#### Step 1.1: Add Django Auth URLs

**File:** `selfbuilding_app/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='editor/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/register/', include('editor.urls')),  # Custom registration
    path('', include('editor.urls')),
]
```

#### Step 1.2: Update Models

**File:** `editor/models.py`

- Add `User` import: `from django.contrib.auth.models import User`
- Add `user` foreign key to: ChatMessage, CodeSnippet, FeatureRequest, CodeExecution
- Create new models: UserProfile, FeatureVersion, TestResult

#### Step 1.3: Create Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 1.4: Update Views

**File:** `editor/views.py`

- Add `@login_required` decorator to all views except login/register
- Filter queries by `request.user`
- Create registration view

#### Step 1.5: Create Templates

**Files:**
- `editor/templates/editor/login.html`
- `editor/templates/editor/register.html`
- Update `editor/templates/editor/index.html` with user info and logout

#### Step 1.6: Update Frontend

**File:** `static/js/main.js`

- Add user context to API calls
- Handle authentication redirects

### Part 2: Version Control Integration (3-4 hours)

#### Step 2.1: Create Git Service

**File:** `editor/git_service.py` (NEW)

```python
import subprocess
from pathlib import Path
from django.conf import settings

class GitService:
    def __init__(self, user):
        self.user = user
        self.branch_name = f"user-{user.id}-workspace"
        self.repo_path = Path(settings.BASE_DIR)
    
    def initialize_user_branch(self):
        """Create user's branch if it doesn't exist"""
        pass
    
    def commit_changes(self, message, files):
        """Commit changes to user's branch"""
        pass
    
    def get_commit_history(self):
        """Get list of commits on user's branch"""
        pass
    
    def checkout_commit(self, commit_hash):
        """Switch to a specific commit"""
        pass
    
    def rollback_to_commit(self, commit_hash):
        """Hard reset to a previous commit"""
        pass
```

#### Step 2.2: Integrate Git into Feature Application

**File:** `editor/views.py`

Update `apply_feature_changes()`:
1. Apply file changes
2. Commit to git
3. Store commit hash in FeatureVersion

#### Step 2.3: Create Version History API

**File:** `editor/views.py`

```python
@login_required
def get_version_history(request):
    """Get user's feature version history"""
    pass

@login_required
def switch_version(request):
    """Switch to a specific version"""
    pass
```

#### Step 2.4: Update Frontend for Version Control

**File:** `static/js/main.js`

- Add version history panel
- Display commit timeline
- Click-to-navigate functionality

### Part 3: Automated Testing & Rollback (3-4 hours)

#### Step 3.1: Create Test Runner Service

**File:** `editor/test_runner.py` (NEW)

```python
import subprocess
from pathlib import Path

class TestRunner:
    def __init__(self, user):
        self.user = user
        self.workspace_path = Path(settings.BASE_DIR)
    
    def detect_test_framework(self):
        """Detect pytest, unittest, or Django tests"""
        pass
    
    def run_tests(self):
        """Execute tests and return results"""
        pass
    
    def parse_test_output(self, stdout, stderr):
        """Parse test output for pass/fail counts"""
        pass
```

#### Step 3.2: Create AI Fix Service

**File:** `editor/test_fixer.py` (NEW)

```python
class TestFixer:
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    def analyze_test_failure(self, test_output, code_files):
        """Use AI to analyze test failures"""
        pass
    
    def generate_fix(self, analysis):
        """Generate code fixes based on failure analysis"""
        pass
```

#### Step 3.3: Implement Testing Workflow

**File:** `editor/views.py`

Create `test_and_apply_feature()`:

```python
def test_and_apply_feature(feature_id, user):
    """
    Complete workflow:
    1. Apply changes
    2. Commit to git
    3. Run tests
    4. If fail -> AI fix -> retry (max 3 times)
    5. If still fail -> rollback
    6. If pass -> mark complete
    """
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        # Run tests
        result = test_runner.run_tests()
        
        if result.passed:
            # Success!
            return success_response
        
        # Tests failed - try AI fix
        iteration += 1
        fix = test_fixer.generate_fix(result)
        # Apply fix and retry
    
    # Max iterations reached - rollback
    git_service.rollback_to_commit(previous_commit)
    return failure_response
```

#### Step 3.4: Update Models

Add test tracking fields to FeatureRequest and create TestResult entries.

#### Step 3.5: Frontend Updates

**File:** `static/js/main.js`

- Display test results in UI
- Show progress during testing
- Notify user of success/failure

---

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/accounts/login/` | GET/POST | User login |
| `/accounts/logout/` | POST | User logout |
| `/accounts/register/` | GET/POST | User registration |

### Version Control Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/versions/` | GET | Get version history |
| `/api/versions/<commit_hash>/` | GET | Get specific version details |
| `/api/versions/switch/` | POST | Switch to version |
| `/api/versions/rollback/` | POST | Rollback to version |

### Testing Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tests/run/` | POST | Run tests for feature |
| `/api/tests/results/<feature_id>/` | GET | Get test results |

### Updated Endpoints (Add User Filtering)

All existing endpoints now filter by `request.user`:
- `/api/chat/`
- `/api/save/`
- `/api/execute/`
- `/api/features/`
- `/api/features/analyze/`
- `/api/features/implement/`
- `/api/features/preview/`
- `/api/features/apply/` → Now includes testing workflow
- `/api/features/reject/`

---

## Frontend Changes

### 1. Login Page (`login.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Login - Self-Building App</title>
    <!-- Dark theme CSS -->
</head>
<body>
    <div class="login-container">
        <h1>Self-Building App</h1>
        <form method="post">
            {% csrf_token %}
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="/accounts/register/">Register</a></p>
    </div>
</body>
</html>
```

### 2. Registration Page (`register.html`)

Similar to login with additional fields.

### 3. Main Page Updates (`index.html`)

Add to header:
```html
<div class="user-info">
    <span>👤 {{ user.username }}</span>
    <a href="/accounts/logout/">Logout</a>
</div>
```

Add version history panel:
```html
<div class="version-panel">
    <h3>📊 Version History</h3>
    <div id="version-timeline"></div>
</div>
```

### 4. JavaScript Updates (`main.js`)

Add functions:
- `loadVersionHistory()`
- `switchToVersion(commitHash)`
- `displayTestResults(results)`
- `showTestingProgress()`

### 5. CSS Updates (`style.css`)

Add styles:
- `.login-container`
- `.user-info`
- `.version-panel`
- `.version-timeline`
- `.test-results`
- `.test-progress`

---

## Testing Strategy

### Unit Tests

**File:** `editor/tests.py`

```python
class AuthenticationTests(TestCase):
    def test_user_registration(self):
        pass
    
    def test_user_login(self):
        pass
    
    def test_data_isolation(self):
        """Ensure users can't see each other's data"""
        pass

class VersionControlTests(TestCase):
    def test_branch_creation(self):
        pass
    
    def test_commit_creation(self):
        pass
    
    def test_version_switching(self):
        pass
    
    def test_rollback(self):
        pass

class AutomatedTestingTests(TestCase):
    def test_test_runner(self):
        pass
    
    def test_fix_generation(self):
        pass
    
    def test_retry_mechanism(self):
        pass
```

### Integration Tests

1. Complete workflow: Register → Login → Request Feature → Review → Apply → Test → Success
2. Failure workflow: Feature → Apply → Test Fail → AI Fix → Retry → Rollback
3. Multi-user isolation: Two users can't modify each other's data

---

## Security Considerations

### 1. Authentication Security

- Use Django's built-in password hashing
- CSRF protection on all forms
- Session timeout configuration
- Secure cookie settings

### 2. Data Isolation

- Always filter by `request.user`
- Never trust client-side user ID
- Use Django's `@login_required` decorator
- Validate user ownership before modifications

### 3. Git Security

- Users can only access their own branches
- Prevent access to main branch
- Validate commit hashes before checkout
- Prevent directory traversal in file paths

### 4. Code Execution Security

- Maintain existing sandboxing
- User-specific execution environments
- Resource limits per user
- Timeout enforcement

---

## Migration Plan

### Step 1: Backup Current Database

```bash
python manage.py dumpdata > backup.json
```

### Step 2: Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Create Default User (for existing data)

```python
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user('admin', 'admin@example.com', 'password')
>>> user.save()
```

### Step 4: Migrate Existing Data

```python
# Assign all existing records to default user
ChatMessage.objects.all().update(user_id=1)
CodeSnippet.objects.all().update(user_id=1)
FeatureRequest.objects.all().update(user_id=1)
CodeExecution.objects.all().update(user_id=1)
```

### Step 5: Initialize Git

```bash
cd /path/to/project
git init
git add .
git commit -m "Initial commit - Phase 5 baseline"
git branch user-1-workspace
```

---

## Success Criteria

Phase 5 is complete when:

- ✅ Users can register and login
- ✅ Each user has isolated data (snippets, chat, features)
- ✅ Git tracks changes per user on separate branches
- ✅ Version history is visible in UI
- ✅ Users can switch between versions
- ✅ Tests run automatically after feature application
- ✅ AI attempts fixes on test failures
- ✅ Rollback works on persistent failures
- ✅ Users receive notifications of test results
- ✅ All existing Phase 1-4 features still work
- ✅ Security review passes
- ✅ Documentation updated

---

## Timeline Estimate

| Task | Time | Dependencies |
|------|------|--------------|
| User Authentication | 2-3 hours | None |
| Model Updates | 1 hour | Authentication |
| Version Control | 3-4 hours | Model Updates |
| Testing Framework | 3-4 hours | Version Control |
| Frontend Updates | 2 hours | All Backend |
| Testing & Debugging | 2-3 hours | All Features |
| Documentation | 1 hour | All Features |
| **Total** | **14-18 hours** | |

---

## Notes

- Start with authentication (foundation for all other features)
- Test thoroughly at each step
- Keep existing Phase 1-4 functionality intact
- Focus on security throughout implementation
- Document all new API endpoints
- Create migration guide for existing users

---

**This implementation plan is ready for development!** 🚀

*Document Version: 1.0*  
*Date: January 28, 2026*  
*Phase: 5 - Planning Complete*
