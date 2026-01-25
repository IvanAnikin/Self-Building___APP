# Technical Documentation - Self-Building App

**Version:** 1.0.0  
**Last Updated:** January 25, 2026  
**Django Version:** 4.2.27  
**Python Version:** 3.9.6

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [Backend Components](#backend-components)
7. [Frontend Components](#frontend-components)
8. [API Endpoints](#api-endpoints)
9. [Internationalization](#internationalization)
10. [Development Workflow](#development-workflow)
11. [Extending the Application](#extending-the-application)

---

## Overview

The Self-Building App is a Django-based web application that provides an interactive code editing environment with an integrated AI chatbot assistant. The application is designed with the concept of "self-building" - users can request features through natural language, and the system is architecturally prepared to process these requests and modify itself dynamically.

### Core Concept

The application follows a unique architectural pattern where:
- Users interact with a code editor (2/3 screen width)
- An AI assistant occupies the remaining space (1/3 screen width)
- Feature requests are captured and stored for processing
- The system is designed to evolve based on user requests

### Current State vs. Vision

**Current Implementation:**
- Functional dark-mode code editor with syntax support
- Working chat interface with message persistence
- Database models for feature tracking (ChatMessage, CodeSnippet, FeatureRequest, CodeExecution)
- Multi-language support (English, Czech, Japanese, Russian)
- AJAX-based communication between frontend and backend
- Sandboxed code execution for Python and JavaScript
- AI-powered feature analysis and code generation (Phase 4 ✅)
- Context-aware code modification with project structure scanning
- Feature request detection and implementation preview system

**Future Vision:**
- Automated application of generated code changes with user approval
- Real-time code modification workflow
- Automated testing of new features
- Version control integration with Git commits
- Rollback mechanism for failed changes

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
├──────────────────────┬──────────────────────────────────┤
│   Code Editor        │       AI Chatbot Interface       │
│   (2/3 width)        │          (1/3 width)             │
└──────────────────────┴──────────────────────────────────┘
           │                          │
           │                          │
           ├────── HTTP/AJAX ─────────┤
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│              Django Web Framework (Backend)              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Views     │  │   URL Router  │  │  Middleware   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│                     ORM Layer                            │
└─────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite Database (db.sqlite3)                │
├─────────────────────────────────────────────────────────┤
│  ChatMessage │ CodeSnippet │ FeatureRequest │ Users     │
└─────────────────────────────────────────────────────────┘
```

### Request Flow

#### Standard Page Load
1. Client requests root URL `/`
2. Django URL dispatcher routes to `editor.views.index`
3. View renders `editor/index.html` template
4. Template includes CSRF token, static files, and i18n tags
5. Browser loads CSS and JavaScript assets
6. JavaScript initializes editor and chat components

#### Chat Message Flow
1. User types message and clicks "Send"
2. JavaScript function `sendMessage()` is triggered
3. AJAX POST request to `/api/chat/` with JSON payload
4. Django view `chat()` processes the message
5. Response JSON returned to client
6. JavaScript updates DOM with new message bubbles

#### Code Save Flow
1. User clicks "Save" button
2. JavaScript captures editor content and filename
3. AJAX POST request to `/api/save/` with JSON payload
4. Django view `save_code()` processes the request
5. (Currently) Acknowledgment returned; (Future) Database persistence
6. Success message displayed in chat interface

---

## Technology Stack

### Backend
- **Framework:** Django 4.2.27
- **Language:** Python 3.9.6
- **Database:** SQLite3 (development)
- **ORM:** Django ORM
- **Server:** Django Development Server (development)

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Custom dark theme, CSS Grid, Flexbox
- **JavaScript (ES6+)** - Vanilla JS, no frameworks
- **AJAX** - Fetch API for asynchronous communication

### Internationalization
- **Django i18n framework**
- **Supported Languages:** English, Czech (cs), Japanese (ja), Russian (ru)
- **Format:** gettext `.po` and `.mo` files

### Development Tools
- **WSGI Server:** Gunicorn (production)
- **ASGI Server:** Daphne (for async features)

---

## Project Structure

```
Self-Building___APP/
│
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── README.md                    # User-facing documentation
├── db.sqlite3                   # SQLite database (generated)
│
├── selfbuilding_app/            # Django project configuration
│   ├── __init__.py             # Python package marker
│   ├── settings.py             # Project settings (SECRET_KEY, DATABASES, etc.)
│   ├── urls.py                 # Root URL configuration with i18n support
│   ├── wsgi.py                 # WSGI application entry point
│   └── asgi.py                 # ASGI application entry point
│
├── editor/                      # Main Django application
│   ├── __init__.py             # Python package marker
│   ├── admin.py                # Django admin configuration
│   ├── apps.py                 # App configuration
│   ├── models.py               # Database models (ChatMessage, CodeSnippet, FeatureRequest)
│   ├── views.py                # Request handlers (index, chat, save_code)
│   ├── urls.py                 # App-specific URL routing
│   ├── tests.py                # Test cases
│   │
│   ├── migrations/             # Database migrations
│   │   ├── __init__.py
│   │   └── 0001_initial.py    # Initial migration (creates all models)
│   │
│   └── templates/              # HTML templates
│       └── editor/
│           └── index.html      # Main application template
│
├── static/                      # Static assets (CSS, JS, images)
│   ├── css/
│   │   └── style.css          # Dark theme styling (390 lines)
│   └── js/
│       └── main.js            # Frontend JavaScript (184 lines)
│
└── locale/                      # Internationalization files
    ├── cs/                      # Czech translations
    │   └── LC_MESSAGES/
    │       ├── django.po        # Translation source
    │       └── django.mo        # Compiled translations
    ├── ja/                      # Japanese translations
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    └── ru/                      # Russian translations
        └── LC_MESSAGES/
            ├── django.po
            └── django.mo
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────┐
│   ChatMessage       │
├─────────────────────┤
│ id (PK)             │
│ message             │
│ response            │
│ timestamp           │
│ is_user             │
└─────────────────────┘

┌─────────────────────┐
│   CodeSnippet       │
├─────────────────────┤
│ id (PK)             │
│ filename            │
│ code                │
│ language            │
│ created_at          │
│ updated_at          │
└─────────────────────┘

┌─────────────────────┐
│  FeatureRequest     │
├─────────────────────┤
│ id (PK)             │
│ description         │
│ status              │
│ created_at          │
│ completed_at        │
└─────────────────────┘

┌─────────────────────┐
│  CodeExecution      │
├─────────────────────┤
│ id (PK)             │
│ code                │
│ language            │
│ filename            │
│ stdout              │
│ stderr              │
│ returncode          │
│ status              │
│ error_message       │
│ executed_at         │
└─────────────────────┘
```

### Model Details

#### ChatMessage Model
**Purpose:** Store conversation history between user and AI assistant

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | Primary Key | Auto-incrementing identifier |
| message | TextField | - | User's input message |
| response | TextField | - | AI assistant's response |
| timestamp | DateTimeField | auto_now_add=True | Message creation time |
| is_user | BooleanField | default=True | Flag to distinguish user vs bot messages |

**Meta Options:**
- `ordering = ['-timestamp']` - Most recent messages first

**File Location:** `editor/models.py` (Lines 3-12)

---

#### CodeSnippet Model
**Purpose:** Persist code saved from the editor

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | Primary Key | Auto-incrementing identifier |
| filename | CharField | max_length=255, default='untitled.txt' | Name of the code file |
| code | TextField | - | Actual code content |
| language | CharField | max_length=50, default='python' | Programming language identifier |
| created_at | DateTimeField | auto_now_add=True | Initial save timestamp |
| updated_at | DateTimeField | auto_now=True | Last modification timestamp |

**Meta Options:**
- `ordering = ['-updated_at']` - Most recently updated first

**File Location:** `editor/models.py` (Lines 14-25)

---

#### FeatureRequest Model
**Purpose:** Track user-requested features and their implementation status

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | Primary Key | Auto-incrementing identifier |
| description | TextField | - | Detailed feature request description |
| status | CharField | max_length=20, choices, default='pending' | Current processing state |
| created_at | DateTimeField | auto_now_add=True | Request submission time |
| completed_at | DateTimeField | null=True, blank=True | Feature completion time |

**Status Choices:**
- `pending` - Awaiting processing
- `processing` - Currently being implemented
- `completed` - Successfully implemented
- `failed` - Implementation failed

**Meta Options:**
- `ordering = ['-created_at']` - Newest requests first

**File Location:** `editor/models.py` (Lines 27-38)

---

#### CodeExecution Model
**Purpose:** Track code execution history, results, and debugging information

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | Primary Key | Auto-incrementing identifier |
| code | TextField | - | The code that was executed |
| language | CharField | max_length=50, default='python' | Programming language |
| filename | CharField | max_length=255, default='untitled.txt' | File name |
| stdout | TextField | blank=True, default='' | Standard output from execution |
| stderr | TextField | blank=True, default='' | Standard error from execution |
| returncode | IntegerField | default=0 | Process return code (0=success) |
| status | CharField | max_length=20, choices | Execution status |
| error_message | TextField | blank=True, default='' | Error details if execution failed |
| executed_at | DateTimeField | auto_now_add=True | Execution timestamp |

**Status Choices:**
- `success` - Execution completed successfully
- `error` - Execution failed with errors

**Meta Options:**
- `ordering = ['-executed_at']` - Most recent executions first

**File Location:** `editor/models.py` (Lines 47-67)

---

### Database Operations

**Migration Files:**
- Initial migration: `editor/migrations/0001_initial.py`
  - Created: January 22, 2026
  - Includes ChatMessage, CodeSnippet, and FeatureRequest models
- Phase 3 migration: `editor/migrations/0002_codeexecution.py`
  - Created: January 24, 2026
  - Adds CodeExecution model for tracking code execution history

**Common Queries:**
```python
# Get recent chat messages
ChatMessage.objects.all()[:10]

# Get latest code snippet
CodeSnippet.objects.first()

# Get pending feature requests
FeatureRequest.objects.filter(status='pending')

# Get feature request by ID and update status
request = FeatureRequest.objects.get(id=1)
request.status = 'processing'
request.save()
```

---

## Backend Components

### Django Settings (`selfbuilding_app/settings.py`)

#### Key Configuration

**Security Settings:**
```python
SECRET_KEY = 'django-insecure-)9*cof^b^kas(*^qp55ntj#p=03(o3_!klk$s$8j*(qw@sinw_'
DEBUG = True  # MUST be False in production
ALLOWED_HOSTS = []  # Add domains in production
```

**Installed Apps:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',      # Admin interface
    'django.contrib.auth',       # Authentication framework
    'django.contrib.contenttypes',
    'django.contrib.sessions',   # Session management
    'django.contrib.messages',   # Messaging framework
    'django.contrib.staticfiles',
    'editor',                    # Custom app
]
```

**Middleware Stack:**
1. `SecurityMiddleware` - Security enhancements
2. `SessionMiddleware` - Session management
3. `LocaleMiddleware` - Language switching (i18n)
4. `CommonMiddleware` - Common utilities
5. `CsrfViewMiddleware` - CSRF protection
6. `AuthenticationMiddleware` - User authentication
7. `MessageMiddleware` - Flash messages
8. `ClickjackingMiddleware` - Clickjacking protection

**Database Configuration:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Internationalization:**
```python
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('cs', _('Czech')),
    ('ja', _('Japanese')),
    ('ru', _('Russian')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
USE_I18N = True
```

**Static Files:**
```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

---

### URL Configuration

#### Root URLs (`selfbuilding_app/urls.py`)

**Pattern Structure:**
```python
# API endpoints without language prefix (fixes 302 redirect issue)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/chat/', editor_views.chat, name='chat'),
    path('api/save/', editor_views.save_code, name='save_code'),
    path('api/execute/', editor_views.execute_code, name='execute_code'),
    # Phase 4: Self-modification endpoints
    path('api/features/', editor_views.list_features, name='list_features'),
    path('api/features/analyze/', editor_views.analyze_feature, name='analyze_feature'),
    path('api/features/implement/', editor_views.implement_feature, name='implement_feature'),
]

# Language-prefixed URLs
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', editor_views.index, name='index'),
)
```

**API Endpoints (No Language Prefix):**

| URL Pattern | View Function | Name | Purpose |
|-------------|---------------|------|---------|
| `'api/chat/'` | `editor_views.chat` | `chat` | Chat message handler |
| `'api/save/'` | `editor_views.save_code` | `save_code` | Code save endpoint |
| `'api/execute/'` | `editor_views.execute_code` | `execute_code` | Code execution endpoint |
| `'api/features/'` | `editor_views.list_features` | `list_features` | List all feature requests |
| `'api/features/analyze/'` | `editor_views.analyze_feature` | `analyze_feature` | Analyze feature feasibility (Phase 4) |
| `'api/features/implement/'` | `editor_views.implement_feature` | `implement_feature` | Generate code for feature (Phase 4) |

**Language-Prefixed URLs:**

| URL Pattern | View Function | Name | Purpose |
|-------------|---------------|------|---------|
| `''` | `editor_views.index` | `index` | Main application page |
| `'admin/'` | `admin.site.urls` | - | Django admin interface |

---

### View Functions (`editor/views.py`)

#### 1. `index(request)`

**Purpose:** Render the main application page

**HTTP Method:** GET

**Implementation:**
```python
def index(request):
    return render(request, 'editor/index.html')
```

**Response:** HTML page with code editor and chatbot

**Template Context:** Empty (all content is static or JavaScript-generated)

---

#### 2. `chat(request)`

**Purpose:** Handle chat messages from the user

**HTTP Method:** POST

**Request Payload:**
```json
{
    "message": "User's message text"
}
```

**Response (Success):**
```json
{
    "status": "success",
    "response": "AI response message"
}
```

**Response (Error):**
```json
{
    "status": "error",
    "message": "Error description"
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad request (invalid JSON)
- 405: Method not allowed (non-POST)

**Implementation Details:**
- Parses JSON from request body
- Currently returns a placeholder response
- Designed for future AI integration
- No database persistence (yet)

**File Location:** `editor/views.py` (Lines 7-25)

---

#### 3. `save_code(request)`

**Purpose:** Handle code save requests from the editor

**HTTP Method:** POST

**Request Payload:**
```json
{
    "code": "# Python code here",
    "filename": "example.py"
}
```

**Response (Success):**
```json
{
    "status": "success",
    "message": "Code saved as example.py"
}
```

**Response (Error):**
```json
{
    "status": "error",
    "message": "Error description"
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad request (invalid JSON)
- 405: Method not allowed (non-POST)

**Implementation Details:**
- Extracts code and filename from JSON
- Currently only acknowledges the save
- Designed for future file system or database persistence
- No actual file writing (yet)

**File Location:** `editor/views.py` (Lines 135-183)

---

#### 4. `execute_code(request)`

**Purpose:** Execute code in sandboxed environment and return results

**HTTP Method:** POST

**Request Payload:**
```json
{
    "code": "print('Hello, World!')",
    "language": "python",
    "filename": "test.py"
}
```

**Response (Success):**
```json
{
    "status": "success",
    "stdout": "Hello, World!\n",
    "stderr": "",
    "returncode": 0,
    "error": null,
    "execution_id": 1
}
```

**Response (Execution Error):**
```json
{
    "status": "error",
    "stdout": "",
    "stderr": "Traceback...\nZeroDivisionError: division by zero",
    "returncode": 1,
    "error": null,
    "execution_id": 2
}
```

**HTTP Status Codes:**
- 200: Request processed (check status field for execution result)
- 400: Bad request (empty code)
- 500: Server error during execution

**Implementation Details:**
- Uses CodeExecutor class for sandboxed execution
- Supports Python 3 and JavaScript (Node.js)
- 5-second timeout protection
- Output truncation at 10,000 characters
- Saves all executions to CodeExecution model
- Returns execution ID for tracking

**File Location:** `editor/views.py` (Lines 185-272)

---

#### 5. `analyze_feature(request)`

**Purpose:** Analyze a feature request and create implementation plan (Phase 4)

**HTTP Method:** POST

**Request Payload:**
```json
{
    "feature_id": 3
}
```

**Response (Success - Feasible):**
```json
{
    "status": "success",
    "analysis": {
        "feasible": true,
        "plan": [
            "Step 1: Modify the HTML template...",
            "Step 2: Update the CSS...",
            "Step 3: Modify the JavaScript..."
        ],
        "files_to_modify": [
            "editor/templates/editor/index.html",
            "static/css/style.css",
            "static/js/main.js"
        ],
        "estimated_complexity": "simple"
    },
    "feature_id": 3
}
```

**Response (Not Feasible):**
```json
{
    "status": "success",
    "analysis": {
        "feasible": false,
        "reason": "Requires external dependencies not available in the project"
    },
    "feature_id": 3
}
```

**HTTP Status Codes:**
- 200: Analysis completed successfully
- 400: Missing feature_id
- 404: Feature request not found
- 500: Analysis error

**Implementation Details:**
- Calls `feature_implementer.analyze_feature_request()`
- Scans project structure before analysis
- Updates FeatureRequest status to 'processing' then 'approved' or 'failed'
- Stores implementation plan as JSON in database
- Uses OpenAI API for intelligent analysis

**File Location:** `editor/views.py` (Lines 276-343)

---

#### 6. `implement_feature(request)`

**Purpose:** Generate code for a feature request (Phase 4)

**HTTP Method:** POST

**Request Payload:**
```json
{
    "feature_id": 3
}
```

**Response (Success):**
```json
{
    "status": "success",
    "message": "Code generated successfully",
    "generated_files": [
        {
            "file": "editor/templates/editor/index.html",
            "code": "<!DOCTYPE html>...",
            "changes": [
                "Added a new div with id 'lineNumbers'",
                "Wrapped textarea in editor-container div"
            ],
            "notes": "Line numbers will be synchronized with editor content"
        }
    ],
    "feature_id": 3
}
```

**Response (Error):**
```json
{
    "status": "error",
    "error": "Feature must be analyzed first"
}
```

**HTTP Status Codes:**
- 200: Code generated successfully
- 400: Missing feature_id or no implementation plan
- 404: Feature request not found
- 500: Code generation error

**Implementation Details:**
- Requires prior analysis (implementation_plan must exist)
- Reads existing file content using `feature_implementer.read_file_safely()`
- Generates context-aware code that preserves existing functionality
- Processes one file at a time (configurable limit)
- Stores generated code in FeatureRequest.generated_code as JSON
- Does NOT automatically apply changes (preview only)

**File Location:** `editor/views.py` (Lines 345-467)

---

#### 7. `list_features(request)`

**Purpose:** List all feature requests with their status

**HTTP Method:** GET

**Response (Success):**
```json
{
    "status": "success",
    "features": [
        {
            "id": 3,
            "description": "Add line numbers on left side of text editor",
            "status": "approved",
            "created_at": "2026-01-25T16:48:50.123456",
            "completed_at": null,
            "has_plan": true,
            "has_code": true
        },
        {
            "id": 2,
            "description": "Add user authentication",
            "status": "pending",
            "created_at": "2026-01-24T10:30:00.000000",
            "completed_at": null,
            "has_plan": false,
            "has_code": false
        }
    ]
}
```

**HTTP Status Codes:**
- 200: Success
- 500: Server error

**Implementation Details:**
- Returns last 20 feature requests
- Includes metadata (has_plan, has_code flags)
- Ordered by creation date (newest first)

**File Location:** `editor/views.py` (Lines 469-494)

---

### Feature Implementer Module (`editor/feature_implementer.py`)

**Purpose:** AI-powered feature analysis and code generation with context awareness (Phase 4)

#### FeatureImplementer Class

**Constructor Parameters:**
- `base_path` (str): Base directory for the project (default: current directory)

**Core Methods:**

##### 1. `scan_project_structure() -> Dict[str, Any]`

Scans project directory and returns comprehensive structure map.

**Returns:**
```python
{
    'python_files': ['manage.py', 'editor/views.py', ...],
    'templates': ['editor/templates/editor/index.html'],
    'static_files': ['static/css/style.css', 'static/js/main.js'],
    'models': ['editor/models.py'],
    'views': ['editor/views.py'],
    'urls': ['selfbuilding_app/urls.py']
}
```

**Features:**
- Skips venv, migrations, __pycache__, .git directories
- Uses exact filename matching to avoid false positives
- Returns relative paths from project root

##### 2. `read_file_safely(file_path: str) -> Dict[str, Any]`

Safely reads file content with size limits and error handling.

**Returns:**
```python
{
    'exists': True,
    'content': 'file content...',
    'error': None
}
```

**Features:**
- 500KB file size limit (configurable via MAX_FILE_SIZE_BYTES)
- Handles encoding errors gracefully
- Returns structured result with error information

##### 3. `analyze_feature_request(description: str) -> Dict[str, Any]`

Analyzes feature request and creates implementation plan using AI.

**Returns:**
```python
{
    'feasible': True,
    'plan': ['Step 1...', 'Step 2...'],
    'files_to_modify': ['editor/templates/editor/index.html'],
    'estimated_complexity': 'simple',
    'reason': None  # or reason if not feasible
}
```

**Features:**
- Scans project structure first
- Provides AI with actual file paths
- Uses OpenAI API with JSON response format
- Temperature: 0.3 (consistent analysis)

##### 4. `generate_code(description, plan, target_file, existing_code) -> Dict[str, Any]`

Generates code for specific file based on feature request.

**Returns:**
```python
{
    'success': True,
    'code': 'complete file content...',
    'changes_made': ['Added line numbers', 'Updated styling'],
    'notes': 'Implementation notes...',
    'preserved': ['Existing functions', 'Django tags']
}
```

**Features:**
- Context-aware: receives existing file content
- Preserves existing functionality when modifying files
- Separate prompts for new vs. modified files
- Temperature: 0.2 (more deterministic code generation)

##### 5-7. Additional Methods

- `preview_changes()`: Generate before/after preview
- `apply_changes()`: Write changes to file with optional backup
- `run_tests()`: Run Django tests to validate changes
- `create_git_commit()`: Create Git commit for changes
- `rollback_changes()`: Rollback to previous state

**Global Instance:**
```python
feature_implementer = FeatureImplementer()
```

**File Location:** `editor/feature_implementer.py` (Lines 1-542)

---

### AI Service Module (`editor/ai_service.py`)

**Purpose:** OpenAI API integration for intelligent chat responses (Phase 2) and feature analysis (Phase 4)

#### AIService Class

**Initialization:**
- Reads `OPENAI_API_KEY` from environment variables
- Sets `enabled` flag based on API key presence
- Uses `gpt-4o-mini` model (configurable via `OPENAI_MODEL` env var)

**Core Methods:**

##### `is_enabled() -> bool`

Returns whether AI service is properly configured with API key.

##### `get_system_prompt() -> str`

Returns the system prompt that defines AI assistant's behavior:
- Help users with coding questions
- Understand feature requests and provide guidance
- Suggest code improvements and best practices
- Be friendly, helpful, and concise

##### `process_message(user_message, conversation_history, code_context) -> Dict`

Processes user message and generates AI response.

**Parameters:**
- `user_message`: The user's input message
- `conversation_history`: Optional list of previous messages (last 10 used for context)
- `code_context`: Optional current code from editor

**Returns:**
```python
{
    'status': 'success',  # or 'fallback' or 'error'
    'response': 'AI response text...',
    'error': None  # or error message if failed
}
```

**Features:**
- Includes conversation history (last 10 messages) for context
- Adds code from editor when provided
- Max tokens: 500
- Temperature: 0.7 (balanced creativity)
- Falls back to keyword-based responses if API unavailable
- Logs token usage to console

##### `_get_fallback_response(user_message) -> str`

Generates keyword-based responses when AI is unavailable:
- Feature request patterns → acknowledgment
- Help patterns → guidance response
- Greeting patterns → friendly hello
- Default → acknowledgment with enhancement note

**Global Instance:**
```python
ai_service = AIService()
```

**File Location:** `editor/ai_service.py` (Lines 1-149)

---

### Code Executor Module (`editor/code_executor.py`)

**Purpose:** Provide secure, sandboxed code execution with timeout and resource limits

#### CodeExecutor Class

**Constructor Parameters:**
- `timeout` (int): Maximum execution time in seconds (default: 5)
- `max_output_length` (int): Maximum output length (default: 10,000)

**Main Methods:**

##### `execute(code: str, language: str) -> Dict[str, Any]`

Executes code in the specified language and returns results.

**Parameters:**
- `code`: Source code to execute
- `language`: Programming language ('python', 'py', 'javascript', 'js', 'node')

**Returns:**
```python
{
    'status': 'success' or 'error',
    'stdout': 'standard output string',
    'stderr': 'standard error string',
    'returncode': 0,  # or error code
    'error': None  # or error message string
}
```

**Supported Languages:**
- Python 3 (via `python3` command)
- JavaScript (via `node` command, if Node.js is installed)

**Security Features:**
1. **Temporary File Isolation**: Code written to temp files, auto-deleted after execution
2. **Timeout Protection**: Processes terminated after timeout expires
3. **Output Truncation**: Long outputs truncated with warning message
4. **Subprocess Sandboxing**: Code runs in separate process with limited environment
5. **Error Handling**: Comprehensive error catching and reporting

**Implementation Details:**
- Uses `subprocess.run()` with timeout
- Creates temporary files with `tempfile.NamedTemporaryFile()`
- Cleans up temp files in finally block
- Sets `PYTHONDONTWRITEBYTECODE=1` for Python to prevent .pyc files

**File Location:** `editor/code_executor.py`

**Global Instance:**
```python
code_executor = CodeExecutor(timeout=5, max_output_length=10000)
```

---

### CSRF Protection

**Mechanism:**
- Django's CSRF middleware generates unique tokens
- Token embedded in HTML via `{% csrf_token %}` template tag
- JavaScript retrieves token from DOM or cookies
- Token included in AJAX request headers

**JavaScript Implementation:**
```javascript
function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;
    
    // Fallback: extract from cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        if (cookie.trim().startsWith('csrftoken=')) {
            return decodeURIComponent(cookie.substring(10));
        }
    }
    return null;
}

// Usage in fetch requests
fetch('/api/chat/', {
    headers: {
        'X-CSRFToken': getCSRFToken()
    }
})
```

---

## Frontend Components

### HTML Template (`editor/templates/editor/index.html`)

#### Template Structure

```html
<!DOCTYPE html>
{% load i18n %}               <!-- Load internationalization -->
{% load static %}             <!-- Load static files -->
{% get_current_language ... %} <!-- Get current language -->
<html lang="{{ LANGUAGE_CODE }}" data-theme="dark">
```

**Key Django Template Tags:**
- `{% trans "Text" %}` - Mark text for translation
- `{% static 'path/to/file' %}` - Generate static file URLs
- `{% csrf_token %}` - Insert CSRF token
- `{% url 'name' %}` - Generate URL from name

#### Layout Sections

**1. Header:**
- Application title and subtitle
- Language switcher dropdown
- Gradient text effects

**2. Main Content (Flex Container):**
- **Editor Section (flex: 2):**
  - Filename input field
  - Save and Run buttons
  - Code textarea with tab support
  
- **Chatbot Section (flex: 1):**
  - Chat message history
  - Input textarea
  - Send button

**3. JavaScript Loading:**
- Single script tag: `{% static 'js/main.js' %}`

---

### CSS Styling (`static/css/style.css`)

#### CSS Architecture

**Design System:**
- CSS Custom Properties (variables)
- Dark theme by default
- Responsive flexbox layouts
- Smooth animations and transitions

**Color Palette:**
```css
:root[data-theme="dark"] {
    --bg-primary: #0d1117;      /* Main background */
    --bg-secondary: #161b22;    /* Card backgrounds */
    --bg-tertiary: #21262d;     /* Elevated elements */
    --text-primary: #c9d1d9;    /* Main text */
    --text-secondary: #8b949e;  /* Secondary text */
    --border-color: #30363d;    /* Borders */
    --accent-primary: #58a6ff;  /* Primary actions */
    --accent-hover: #1f6feb;    /* Hover states */
    --success: #3fb950;         /* Success states */
    --danger: #f85149;          /* Error states */
    --editor-bg: #0d1117;       /* Code editor */
}
```

**Layout System:**
- Main content: `display: flex` with 2:1 ratio
- Editor section: `flex: 2` (66.67% width)
- Chatbot section: `flex: 1` (33.33% width)
- Responsive: Stacks vertically on screens < 1024px

**Typography:**
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 
                 'Segoe UI', 'Noto Sans', 
                 Helvetica, Arial, sans-serif;
}

.editor {
    font-family: 'Consolas', 'Monaco', 
                 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
}
```

**Animations:**
- Message fade-in: 0.3s ease-in
- Button hover lift: translateY(-1px)
- Loading spinner: 0.8s rotation
- Smooth transitions: 0.2s on interactive elements

**Accessibility:**
- Focus states with blue outline
- Semantic HTML5 elements
- ARIA-compatible structure
- High contrast ratios

**File Location:** `static/css/style.css` (390 lines)

---

### JavaScript (`static/js/main.js`)

#### Module Structure

**1. Initialization**
```javascript
const editor = document.getElementById('editor');
const filenameInput = document.getElementById('filename');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
```

**2. CSRF Token Management**

Function: `getCSRFToken()`
- Checks DOM for `[name=csrfmiddlewaretoken]`
- Falls back to cookie parsing
- Returns token string or null

**3. Editor Functionality**

**Tab Key Handler:**
```javascript
editor.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        e.preventDefault();  // Prevent focus change
        // Insert 4 spaces at cursor position
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + 
                     '    ' + 
                     this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
    }
});
```

**4. Chat Interface**

**Add Message Function:**
```javascript
function addMessage(content, isUser = false)
```
- Creates message DOM elements
- Applies appropriate CSS classes
- Auto-scrolls to bottom
- Handles both user and bot messages

**Typing Indicator:**
```javascript
function showTypingIndicator()  // Shows "Thinking..." message
function removeTypingIndicator() // Removes typing indicator
```

**Send Message Function:**
```javascript
async function sendMessage()
```
**Flow:**
1. Validate input (non-empty)
2. Display user message
3. Clear input field
4. Show typing indicator
5. Disable send button
6. POST to `/api/chat/` with JSON payload
7. Parse response
8. Remove typing indicator
9. Display bot response
10. Re-enable send button
11. Error handling with try/catch

**5. Code Operations**

**Save Button:**
- Captures editor content and filename
- POSTs to `/api/save/`
- Displays success/error in chat
- No actual file persistence yet

**Run Button:**
- Currently shows placeholder message
- Prepared for future code execution feature

**File Location:** `static/js/main.js` (184 lines)

---

## API Endpoints

### Endpoint Summary Table

| Endpoint | Method | Auth | Rate Limit | Purpose |
|----------|--------|------|------------|---------|
| `/api/chat/` | POST | None | None | Process chat messages |
| `/api/save/` | POST | None | None | Save code snippets |
| `/i18n/setlang/` | POST | None | None | Switch language |

---

### 1. Chat API

**Endpoint:** `/api/chat/`

**Method:** POST

**Content-Type:** application/json

**Request Headers:**
```
Content-Type: application/json
X-CSRFToken: <token>
```

**Request Body:**
```json
{
    "message": "Add user authentication to the app"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "response": "I received your request: 'Add user authentication to the app'. In the future, I will be able to help you modify the app based on your requirements. This feature is under development."
}
```

**Error Response (400):**
```json
{
    "status": "error",
    "message": "Invalid JSON"
}
```

**Error Response (405):**
```json
{
    "status": "error",
    "message": "Only POST requests are allowed"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{"message":"Add dark mode"}'
```

---

### 2. Save Code API

**Endpoint:** `/api/save/`

**Method:** POST

**Content-Type:** application/json

**Request Headers:**
```
Content-Type: application/json
X-CSRFToken: <token>
```

**Request Body:**
```json
{
    "code": "def hello():\n    print('Hello World')",
    "filename": "hello.py"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "message": "Code saved as hello.py"
}
```

**Error Response (400):**
```json
{
    "status": "error",
    "message": "Invalid JSON"
}
```

**Error Response (405):**
```json
{
    "status": "error",
    "message": "Only POST requests are allowed"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/save/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{"code":"print(\"test\")","filename":"test.py"}'
```

---

### 3. Execute Code API

**Endpoint:** `/api/execute/`

**Method:** POST

**Content-Type:** application/json

**Request Headers:**
```
Content-Type: application/json
X-CSRFToken: <token>
```

**Request Body:**
```json
{
    "code": "print('Hello, World!')\nprint(2 + 2)",
    "language": "python",
    "filename": "test.py"
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "stdout": "Hello, World!\n4\n",
    "stderr": "",
    "returncode": 0,
    "error": null,
    "execution_id": 1
}
```

**Error Response - Execution Failed (200):**
```json
{
    "status": "error",
    "stdout": "",
    "stderr": "Traceback (most recent call last):\n  File \"/tmp/xyz.py\", line 1\n    x = 10 / 0\nZeroDivisionError: division by zero",
    "returncode": 1,
    "error": null,
    "execution_id": 2
}
```

**Error Response - Empty Code (400):**
```json
{
    "status": "error",
    "error": "Code cannot be empty",
    "stdout": "",
    "stderr": ""
}
```

**Error Response - Unsupported Language (200):**
```json
{
    "status": "error",
    "error": "Unsupported language: rust. Currently supported: Python, JavaScript",
    "stdout": "",
    "stderr": "",
    "returncode": -1,
    "execution_id": 3
}
```

**Error Response - Timeout (200):**
```json
{
    "status": "error",
    "error": "Execution timeout: Code took longer than 5 seconds",
    "stdout": "",
    "stderr": "",
    "returncode": -1,
    "execution_id": 4
}
```

**Supported Languages:**
- `python` or `py` - Python 3 execution
- `javascript`, `js`, or `node` - Node.js execution

**Security Features:**
- 5-second execution timeout
- Output truncation at 10,000 characters
- Temporary file cleanup
- Sandboxed subprocess execution

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/execute/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{"code":"print(\"Hello\")", "language":"python", "filename":"test.py"}'
```

---

## Internationalization

### Supported Languages

| Language | Code | Translation Files |
|----------|------|-------------------|
| English | en | (default, no files needed) |
| Czech | cs | locale/cs/LC_MESSAGES/django.po, .mo |
| Japanese | ja | locale/ja/LC_MESSAGES/django.po, .mo |
| Russian | ru | locale/ru/LC_MESSAGES/django.po, .mo |

### Translation Workflow

**1. Mark Strings for Translation:**
```python
# In Python code
from django.utils.translation import gettext_lazy as _
message = _("Hello, World!")

# In templates
{% load i18n %}
{% trans "Save" %}
```

**2. Extract Messages:**
```bash
python manage.py makemessages -l cs
python manage.py makemessages -l ja
python manage.py makemessages -l ru
```

**3. Translate Strings:**
Edit `locale/<lang>/LC_MESSAGES/django.po`:
```po
msgid "Save"
msgstr "Uložit"  # Czech translation
```

**4. Compile Messages:**
```bash
python manage.py compilemessages
```

### Language Switching

**User Interface:**
- Dropdown in header
- Form submission to `/i18n/setlang/`
- Sets `django_language` cookie
- Redirects to same page with language prefix

**Backend Implementation:**
```python
# settings.py
LANGUAGE_CODE = 'en'
USE_I18N = True
MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',  # Language detection
    # ...
]

# urls.py
from django.conf.urls.i18n import i18n_patterns
urlpatterns += i18n_patterns(
    path('', include('editor.urls')),
)
```

---

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd Self-Building___APP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Database Migrations

**Creating Migrations:**
```bash
# After modifying models.py
python manage.py makemigrations editor

# Apply migrations
python manage.py migrate

# View SQL for migration
python manage.py sqlmigrate editor 0001

# Show migration status
python manage.py showmigrations
```

**Migration Best Practices:**
- Always review generated migrations
- Test migrations on a copy of production data
- Use `RunPython` for data migrations
- Never edit applied migrations

### Adding Static Files

**Process:**
1. Add file to `static/css/` or `static/js/`
2. Reference in template: `{% static 'path/to/file' %}`
3. For production, run: `python manage.py collectstatic`

### Django Admin

**Access:** http://localhost:8000/admin/

**Registering Models:**
```python
# editor/admin.py
from django.contrib import admin
from .models import ChatMessage, CodeSnippet, FeatureRequest

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('message', 'timestamp', 'is_user')
    list_filter = ('is_user', 'timestamp')
    search_fields = ('message', 'response')

admin.site.register(CodeSnippet)
admin.site.register(FeatureRequest)
```

### Testing

**Running Tests:**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test editor

# Run with verbosity
python manage.py test --verbosity=2

# Keep test database
python manage.py test --keepdb
```

**Writing Tests:**
```python
# editor/tests.py
from django.test import TestCase, Client
from .models import ChatMessage

class ChatViewTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_chat_endpoint_post(self):
        response = self.client.post('/api/chat/', {
            'message': 'Test message'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
```

---

## Extending the Application

### Adding a New View

**1. Define view in `editor/views.py`:**
```python
def new_feature(request):
    if request.method == 'POST':
        # Handle POST request
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)
```

**2. Add URL pattern in `editor/urls.py`:**
```python
urlpatterns = [
    # ...
    path('api/new-feature/', views.new_feature, name='new_feature'),
]
```

**3. Call from JavaScript:**
```javascript
fetch('/api/new-feature/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ data: 'value' })
})
```

### Adding a New Model

**1. Define model in `editor/models.py`:**
```python
class NewModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
```

**2. Create and apply migration:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**3. Register in admin:**
```python
# editor/admin.py
from .models import NewModel
admin.site.register(NewModel)
```

### Adding AI Integration

**Recommended Architecture:**

**1. Create AI service module:**
```python
# editor/ai_service.py
import openai  # or other AI library

class AIAssistant:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def process_request(self, user_message):
        # Call AI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        return response.choices[0].message.content
```

**2. Update chat view:**
```python
from .ai_service import AIAssistant

def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        # Use AI service
        ai = AIAssistant(api_key=settings.OPENAI_API_KEY)
        response_message = ai.process_request(user_message)
        
        # Save to database
        ChatMessage.objects.create(
            message=user_message,
            response=response_message,
            is_user=False
        )
        
        return JsonResponse({
            'status': 'success',
            'response': response_message
        })
```

**3. Add API key to settings:**
```python
# settings.py
import os
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
```

### Adding Code Execution

**Security Considerations:**
- ⚠️ Never execute arbitrary code without sandboxing
- Use containers (Docker) or VMs
- Implement timeout mechanisms
- Restrict filesystem access
- Monitor resource usage

**Recommended Approach:**
```python
# editor/code_executor.py
import subprocess
import tempfile
import os

class CodeExecutor:
    def __init__(self, timeout=5):
        self.timeout = timeout
    
    def execute_python(self, code):
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Execute with timeout
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout'}
        finally:
            os.unlink(temp_path)
```

### Adding User Authentication

**1. Use Django's built-in auth:**
```python
# editor/views.py
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'editor/index.html')
```

**2. Add login URLs:**
```python
# selfbuilding_app/urls.py
from django.contrib.auth import views as auth_views

urlpatterns += [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

**3. Associate models with users:**
```python
# editor/models.py
from django.contrib.auth.models import User

class CodeSnippet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # ... other fields
```

---

## Production Deployment Checklist

### Security

- [ ] Change `SECRET_KEY` to environment variable
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Enable CSRF protection (already enabled)
- [ ] Implement rate limiting
- [ ] Configure CORS if needed
- [ ] Use secure session cookies
- [ ] Enable security headers (HSTS, CSP, etc.)

### Database

- [ ] Switch from SQLite to PostgreSQL/MySQL
- [ ] Configure database backups
- [ ] Set up connection pooling
- [ ] Optimize database indexes
- [ ] Run `python manage.py check --deploy`

### Static Files

- [ ] Run `python manage.py collectstatic`
- [ ] Serve static files via CDN or Nginx
- [ ] Enable gzip compression
- [ ] Configure cache headers

### Performance

- [ ] Use production WSGI server (Gunicorn)
- [ ] Configure reverse proxy (Nginx)
- [ ] Enable Redis for caching
- [ ] Implement database query optimization
- [ ] Use Celery for background tasks

### Monitoring

- [ ] Set up logging (Django + Gunicorn)
- [ ] Configure error tracking (Sentry)
- [ ] Monitor performance (New Relic, DataDog)
- [ ] Set up uptime monitoring
- [ ] Configure automated backups

---

## Troubleshooting

### Common Issues

**1. CSRF Token Missing**
- **Symptom:** 403 Forbidden on POST requests
- **Solution:** Ensure `{% csrf_token %}` in form, check JavaScript getCSRFToken()

**2. Static Files Not Loading**
- **Symptom:** 404 on CSS/JS files
- **Solution:** Run `python manage.py collectstatic`, check `STATIC_URL` setting

**3. Database Locked (SQLite)**
- **Symptom:** "database is locked" error
- **Solution:** Switch to PostgreSQL for concurrent access

**4. Migration Conflicts**
- **Symptom:** Migration errors after git pull
- **Solution:** Run `python manage.py migrate --fake` carefully, or reset migrations

**5. Language Not Switching**
- **Symptom:** UI stays in one language
- **Solution:** Check `LocaleMiddleware` order, run `compilemessages`

---

## Performance Considerations

### Current Limitations

- **SQLite:** Not suitable for high-concurrency production
- **No Caching:** Every request hits database/filesystem
- **Synchronous Views:** Blocking I/O operations
- **No Load Balancing:** Single server instance

### Optimization Strategies

**1. Database:**
- Migrate to PostgreSQL
- Add database indexes on frequently queried fields
- Use `select_related()` and `prefetch_related()` for ORM queries

**2. Caching:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# In views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def index(request):
    return render(request, 'editor/index.html')
```

**3. Async Views (Django 4.1+):**
```python
import asyncio
from django.http import JsonResponse

async def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        response = await process_message_async(data['message'])
        return JsonResponse({'status': 'success', 'response': response})
```

---

## Architecture Decisions

### Why Django?

**Pros:**
- Batteries-included framework (ORM, admin, auth)
- Excellent documentation
- Large ecosystem
- Built-in security features
- Rapid development

**Cons:**
- Monolithic (harder to microservice-ize)
- Python Global Interpreter Lock (GIL) for CPU-bound tasks

### Why SQLite (Development)?

**Pros:**
- Zero configuration
- File-based (easy backup)
- Perfect for development
- Built into Python

**Cons:**
- Limited concurrency
- Not suitable for production
- No user management
- Size limitations

### Why Vanilla JavaScript?

**Pros:**
- No build step required
- Faster initial load
- Simpler debugging
- No dependency management

**Cons:**
- More verbose than frameworks
- Manual DOM manipulation
- No component reusability
- State management complexity at scale

**Future Consideration:** Migrate to React/Vue for complex features

---

## Future Roadmap

### Phase 1: Foundation ✅ **COMPLETED**
- ✅ Basic code editor with tab support and monospace font
- ✅ Chat interface with typing indicators and message history
- ✅ Multi-language support (English, Czech, Japanese, Russian)
- ✅ Database models (ChatMessage, CodeSnippet, FeatureRequest)
- ✅ CSRF protection and secure API endpoints
- ✅ Responsive dark mode UI

### Phase 2: AI Integration ✅ **COMPLETED**
- ✅ Connected to OpenAI API (gpt-4o-mini)
- ✅ Implemented context-aware responses with conversation history
- ✅ Added conversation memory (last 10 messages)
- ✅ Feature request parsing and detection
- ✅ Environment variable configuration (.env)
- ✅ Graceful fallback when API unavailable
- ✅ Database persistence of all conversations
- ✅ Token usage tracking and monitoring

### Phase 3: Code Execution ✅ **COMPLETED**
- ✅ Sandboxed Python execution
- ✅ Output display in UI (dedicated collapsible panel)
- ✅ Multiple language support (Python 3, JavaScript/Node.js)
- ✅ Error handling and debugging (full traceback display)
- ✅ Timeout and resource limits (5-second timeout, 10KB output limit)
- ✅ CodeExecutor module with security features
- ✅ CodeExecution model for history tracking
- ✅ Comprehensive test suite (11 tests)
- [ ] Real-time output streaming (future enhancement)

### Phase 4: Self-Modification ✅ **PARTS 1-2 COMPLETED**
- ✅ **Part 1:** Feature request detection and automatic tracking
- ✅ **Part 1:** Feasibility analysis with project structure scanning
- ✅ **Part 2:** AI-powered code generation from natural language
- ✅ **Part 2:** Context-aware code modification
- ✅ **Part 2:** Implementation preview system
- ✅ **Part 2:** FeatureImplementer service with 7 core methods
- ✅ **Part 2:** Three API endpoints (analyze, implement, list)
- ✅ **Part 2:** Safe file reading with size limits
- ✅ **Part 2:** Project structure scanner
- ✅ **Part 2:** Generated code preview with changes tracking
- ⏳ **Part 3:** Automated file modification with user approval workflow (NEXT PRIORITY)

### Phase 5: Advanced Features (Future)
- User authentication and authorization
- Version control integration (Git commits)
- Automated testing framework
- Rollback mechanism for failed changes

### Phase 6: Collaboration (Optional)
- Project sharing and permissions
- Real-time collaboration (WebSockets)
- Code review system
- Team workspaces
- Activity feeds and notifications

---

## Contributing Guidelines

### Code Style

**Python (PEP 8):**
- 4 spaces for indentation
- Max line length: 79 characters
- Use descriptive variable names
- Add docstrings to functions

**JavaScript:**
- 2 or 4 spaces (consistent)
- Use `const` and `let` (no `var`)
- Semicolons recommended
- CamelCase for functions

**CSS:**
- Use CSS variables for theming
- Mobile-first approach
- Avoid `!important`
- Organize by component

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add: New feature description"

# Push and create pull request
git push origin feature/new-feature
```

**Commit Message Format:**
- `Add: New feature`
- `Fix: Bug description`
- `Update: Modification description`
- `Refactor: Code improvement`
- `Docs: Documentation update`

---

## Glossary

| Term | Definition |
|------|------------|
| **ASGI** | Asynchronous Server Gateway Interface - async Python web server standard |
| **CSRF** | Cross-Site Request Forgery - security vulnerability/protection mechanism |
| **Django ORM** | Object-Relational Mapping - database abstraction layer |
| **i18n** | Internationalization - supporting multiple languages |
| **Middleware** | Software layer that processes requests/responses |
| **Migration** | Database schema change file |
| **Template Tag** | Django template language syntax for dynamic content |
| **View** | Python function/class that handles HTTP requests |
| **WSGI** | Web Server Gateway Interface - Python web server standard |

---

## References

- **Django Documentation:** https://docs.djangoproject.com/
- **Django i18n:** https://docs.djangoproject.com/en/stable/topics/i18n/
- **Django REST Framework:** https://www.django-rest-framework.org/
- **MDN Web Docs:** https://developer.mozilla.org/
- **PEP 8 Style Guide:** https://pep8.org/

---

## Contact & Support

For questions about this technical documentation or the project architecture, please refer to the main [README.md](README.md) or create an issue in the project repository.

**Last Updated:** January 22, 2026  
**Documentation Version:** 1.0.0  
**Project Version:** 1.0.0
