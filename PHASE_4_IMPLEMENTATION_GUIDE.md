# Phase 4 Part 2: Context-Aware Code Modification Implementation Guide

**Priority:** HIGH  
**Status:** Not Started  
**Complexity:** Medium  
**Estimated Time:** 2-4 hours

---

## Problem Statement

Currently, the feature implementation system generates code **without context** of the existing application:

### Current Issues ❌
1. **No file reading**: Doesn't check if files exist or read their current content
2. **Blind generation**: AI generates brand new files from scratch without knowing existing code structure
3. **Wrong file paths**: Generates incorrect file names (e.g., `templates/editor.html` instead of `templates/editor/index.html`)
4. **No preservation**: Can't preserve existing functions, imports, or critical code
5. **No diff support**: Can't show what actually changed
6. **Overwrites everything**: Would destroy existing code if applied

### Example of Current Behavior
When asked to "add syntax highlighting to editor":
- AI generates: `templates/editor.html` (new file, wrong location)
- Should modify: `templates/editor/index.html` (existing file)
- Doesn't know: What's already in the file, Django template structure, existing JavaScript

---

## Solution: Context-Aware Code Generation

### Required Context Information

The AI needs to know:

#### 1. **Project Structure**
```
- List of all Python files
- List of all templates
- List of all static files (JS, CSS)
- Directory structure
```

#### 2. **Target File Context**
```
- Does the file exist?
- Current file content (if exists)
- File type (Python, HTML, CSS, JS)
- Related files (imports, includes)
```

#### 3. **Project Metadata**
```
- Django version
- Installed apps
- URL patterns
- Model definitions
- Existing API endpoints
```

---

## Implementation Steps

### Step 1: Add Project Scanner Method

**File:** `editor/feature_implementer.py`

**Location:** Add new method to `FeatureImplementer` class (around line 100)

```python
def scan_project_structure(self) -> Dict[str, Any]:
    """
    Scan the project directory and return a comprehensive structure map.
    
    Returns:
        Dictionary containing:
        {
            'python_files': List[str],
            'templates': List[str],
            'static_files': List[str],
            'models': List[str],
            'views': List[str],
            'urls': List[str]
        }
    """
    structure = {
        'python_files': [],
        'templates': [],
        'static_files': [],
        'models': [],
        'views': [],
        'urls': []
    }
    
    # Scan Python files
    for root, dirs, files in os.walk(self.base_path):
        # Skip venv, migrations, __pycache__
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'migrations', '.git']]
        
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), self.base_path)
            
            if file.endswith('.py'):
                structure['python_files'].append(rel_path)
                if 'models.py' in file:
                    structure['models'].append(rel_path)
                elif 'views.py' in file:
                    structure['views'].append(rel_path)
                elif 'urls.py' in file:
                    structure['urls'].append(rel_path)
            
            elif file.endswith('.html'):
                structure['templates'].append(rel_path)
            
            elif file.endswith(('.js', '.css', '.jpg', '.png', '.svg')):
                structure['static_files'].append(rel_path)
    
    return structure
```

### Step 2: Add File Reader Method

**File:** `editor/feature_implementer.py`

**Location:** Add after `scan_project_structure` method

```python
def read_file_safely(self, file_path: str) -> Dict[str, Any]:
    """
    Safely read a file's content.
    
    Args:
        file_path: Relative path to file from project root
        
    Returns:
        Dictionary with:
        {
            'exists': bool,
            'content': str (if exists),
            'error': str (if failed)
        }
    """
    try:
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return {
                'exists': False,
                'content': None,
                'error': f'File {file_path} does not exist'
            }
        
        # Don't read binary files or very large files
        if full_path.stat().st_size > 500000:  # 500KB limit
            return {
                'exists': True,
                'content': None,
                'error': 'File too large to read'
            }
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'exists': True,
            'content': content,
            'error': None
        }
        
    except Exception as e:
        return {
            'exists': False,
            'content': None,
            'error': f'Error reading file: {str(e)}'
        }
```

### Step 3: Enhance Feasibility Analysis

**File:** `editor/feature_implementer.py`

**Method:** `analyze_feature_request` (line ~40)

**Change:** Add project context to the AI prompt

```python
def analyze_feature_request(self, description: str) -> Dict[str, Any]:
    """Analyze a feature request with full project context."""
    
    if not self.ai_service.is_enabled():
        return {
            'feasible': False,
            'reason': 'AI service is not enabled. Please configure OpenAI API key.'
        }
    
    # NEW: Scan project structure
    project_structure = self.scan_project_structure()
    
    prompt = f"""Analyze the following feature request for a Django web application (Self-Building App):

Feature Request: {description}

Current Project Structure:
- Django backend (Python)
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Database: SQLite with Django ORM

Existing Files:
Python Files: {', '.join(project_structure['python_files'][:20])}
Templates: {', '.join(project_structure['templates'])}
Static Files: {', '.join(project_structure['static_files'][:20])}

Existing models: ChatMessage, CodeSnippet, FeatureRequest, CodeExecution
Existing features: Code editor, AI chatbot, Code execution (Python/JS)

IMPORTANT: Use ONLY the actual file paths listed above. Do not invent new file names.

Please provide:
1. Feasibility assessment (is this implementable?)
2. Implementation plan (step-by-step)
3. List of EXISTING files that need modification (choose from files listed above)
4. Estimated complexity (simple/medium/complex)
5. Any dependencies or prerequisites

Respond in JSON format:
{{
    "feasible": true/false,
    "plan": ["step 1", "step 2", ...],
    "files_to_modify": ["actual/file/path.py"],
    "estimated_complexity": "simple|medium|complex",
    "reason": "explanation if not feasible"
}}"""
    
    # Rest of method stays the same...
```

### Step 4: Fix Code Generation to Read Existing Files

**File:** `editor/views.py`

**Method:** `implement_feature` (line ~370)

**Change:** Read existing file content before generating code

```python

max_files_to_process = 5
for file_path in files_to_modify[:max_files_to_process]:
    print(f"📝 Generating code for {file_path}...")
    
    # NEW: Read existing file content
    from pathlib import Path
    existing_code = None
    full_path = Path(settings.BASE_DIR) / file_path
    
    if full_path.exists():
        print(f"✅ File exists, reading current content...")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                existing_code = f.read()
            print(f"📖 Read {len(existing_code)} characters from existing file")
        except Exception as e:
            print(f"⚠️  Could not read file: {e}")
    else:
        print(f"ℹ️  File does not exist, will generate new file")
    
    # MODIFIED: Pass existing code to generate_code
    result = feature_implementer.generate_code(
        feature.description,
        feature.implementation_plan,
        file_path,
        existing_code=existing_code  # NEW: Pass existing code
    )
```

### Step 5: Improve AI Prompt in generate_code

**File:** `editor/feature_implementer.py`

**Method:** `generate_code` (line ~107)

**Change:** Enhance prompt with clearer instructions

```python
# Build existing code section separately to avoid f-string backslash issue
existing_code_section = ""
if existing_code:
    existing_code_section = f"""
Current File Content:
```
{existing_code}
```

IMPORTANT: Modify the existing code above to add the requested feature.
- Preserve all existing functionality
- Maintain existing imports, functions, and structure
- Only add/modify what's necessary for the new feature
- Keep the same file format and style
"""
else:
    existing_code_section = """
This is a NEW file that does not exist yet.
Generate complete, production-ready code.
"""

modified_or_new = "modified" if existing_code else "new"

prompt = f"""Generate code for this Django application feature:

Feature: {feature_description}

Implementation Plan: {implementation_plan}

Target File: {target_file}
Mode: {mode}

{existing_code_section}

Generate the complete {modified_or_new} file content for {target_file}.
Follow Django best practices and maintain code quality.
Ensure the code integrates seamlessly with the existing application.

If modifying existing code:
- Preserve all critical functionality
- Keep existing imports and structure
- Comment your changes with # NEW: or # MODIFIED:

Respond in JSON format:
{{
    "code": "complete file content",
    "changes_made": ["list of key changes"],
    "notes": "important implementation notes",
    "preserved": ["list of things preserved from original"]
}}"""
```

---

## Testing Steps

### 1. Test Project Structure Scanning
```python
from editor.feature_implementer import feature_implementer
structure = feature_implementer.scan_project_structure()
print(f"Found {len(structure['python_files'])} Python files")
print(f"Found {len(structure['templates'])} templates")
```

### 2. Test File Reading
```python
result = feature_implementer.read_file_safely('templates/editor/index.html')
print(f"File exists: {result['exists']}")
print(f"Content length: {len(result['content']) if result['content'] else 0}")
```

### 3. Test Feature Analysis with Context
- Create new feature request: "Add line numbers to the code editor"
- Click analyze
- Check that AI mentions actual existing files
- Verify it knows about `templates/editor/index.html` not `templates/editor.html`

### 4. Test Code Generation with Existing Content
- Request feature that modifies existing file
- Verify generated code preserves existing structure
- Check that it shows what was changed vs preserved

---

## Expected Outcomes

After implementation:

✅ AI knows all files in the project  
✅ AI reads existing file content before modifying  
✅ AI uses correct file paths from actual project structure  
✅ Generated code preserves existing functionality  
✅ Can see what changed (diff-like output)  
✅ Much more accurate and safe code generation  

---

## Files to Modify

1. **`editor/feature_implementer.py`**
   - Add `scan_project_structure()` method
   - Add `read_file_safely()` method
   - Modify `analyze_feature_request()` to include project context
   - Enhance `generate_code()` prompt

2. **`editor/views.py`**
   - Modify `implement_feature()` to read existing files
   - Add import for Path and settings
   - Add debug logging for file reading

---

## Additional Improvements (Optional)

### Add Diff Generation
Show what changed in a readable format:

```python
def generate_diff(self, original: str, modified: str) -> str:
    """Generate a unified diff between original and modified code."""
    import difflib
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile='original',
        tofile='modified'
    )
    return ''.join(diff)
```

### Add File Backup Before Modification
```python
def backup_file(self, file_path: str) -> str:
    """Create a backup of file before modifying."""
    import shutil
    from datetime import datetime
    
    backup_dir = self.base_path / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{file_path.replace('/', '_')}_{timestamp}.bak"
    
    shutil.copy2(self.base_path / file_path, backup_path)
    return str(backup_path)
```

---

## Success Criteria

- [ ] `scan_project_structure()` method implemented and tested
- [ ] `read_file_safely()` method implemented and tested
- [ ] Feature analysis includes actual project structure
- [ ] Code generation reads existing files
- [ ] AI uses correct file paths from project
- [ ] Generated code preserves existing functionality
- [ ] Manual testing shows improved accuracy
- [ ] Documentation updated

---

## Notes for Implementation

- Import `os` and `Path` at top of `feature_implementer.py`
- Add `from django.conf import settings` in `views.py`
- Test incrementally - add one method at a time
- Use print statements for debugging
- Check terminal logs to verify context is being passed
- Compare before/after AI prompts to ensure context is included

---

**This guide is ready for a GitHub Copilot agent or human developer to implement the context-aware code modification system.**
