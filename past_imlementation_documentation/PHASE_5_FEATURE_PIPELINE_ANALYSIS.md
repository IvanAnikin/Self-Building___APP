# Phase 5 Feature Development Pipeline — Analysis & Improvement Plan

## Table of Contents
1. [Current Approach](#current-approach)
2. [Real-World Case Study](#real-world-case-study)
3. [Identified Problems](#identified-problems)
4. [Proposed Improvements](#proposed-improvements)
5. [Target Architecture](#target-architecture)
6. [Implementation Roadmap](#implementation-roadmap)

---

## Current Approach

### How Feature Requests Flow Through the System

The self-building app's core capability — letting users request features in natural language and having AI implement them — follows this pipeline:

```
User message
    │
    ▼
┌──────────────────────────────────────────────┐
│  1. DETECTION  (_is_feature_request)         │
│     16 substring patterns matched against    │
│     the user's chat message                  │
│     e.g. "add a", "implement", "create a"   │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│  2. ANALYSIS  (analyze_feature_request)      │
│     • Scans project directory structure      │
│     • Sends file listing + request to GPT    │
│     • AI returns JSON:                       │
│       - feasible: bool                       │
│       - plan: step-by-step list              │
│       - files_to_modify: [file paths]        │
│       - estimated_complexity: simple/med/cmplx│
│     • max_completion_tokens: 1000            │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│  3. CODE GENERATION  (generate_code)         │
│     FOR EACH file in files_to_modify[:5]:    │
│       • Read existing file content           │
│       • Send to GPT with feature description │
│       • AI returns complete file content     │
│       • max_completion_tokens: 4000          │
│     ⚠ Each file generated independently     │
│     ⚠ No cross-file context passed          │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│  4. PREVIEW & DIFF                           │
│     • Generate unified diff per file         │
│     • Show additions/deletions count         │
│     • Present to user in the UI              │
└──────────────────────────┬───────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────┐
│  5. USER APPROVAL                            │
│     User reviews diff and clicks             │
│     "Accept" or "Reject"                     │
└──────────────────────────┬───────────────────┘
                           │ (if accepted)
                           ▼
┌──────────────────────────────────────────────┐
│  6. APPLY CHANGES  (apply_changes)           │
│     • Create .backup of original file        │
│     • Overwrite file with generated content  │
│     • Git commit on user's branch            │
└──────────────────────────────────────────────┘
```

### Key Code Locations

| Component | File | Function / Line |
|-----------|------|-----------------|
| Feature detection | `editor/views.py` | `_is_feature_request()` — line 225 |
| Feature analysis | `editor/feature_implementer.py` | `analyze_feature_request()` — line 133 |
| Code generation | `editor/feature_implementer.py` | `generate_code()` — line 250 |
| File-level orchestration | `editor/views.py` | `implement_feature()` — line 446 |
| Diff generation | `editor/feature_implementer.py` | `generate_diff()` — line 385 |
| File application | `editor/feature_implementer.py` | `apply_changes()` — line 435 |

### Current Constants & Limits

| Parameter | Value | Location |
|-----------|-------|----------|
| Max files in prompt | 20 | `feature_implementer.py` line 15 |
| Max file size to read | 500 KB | `feature_implementer.py` line 14 |
| Max files to process per feature | 5 | `views.py` line 513 |
| Analysis token limit | 1,000 | `feature_implementer.py` (analyze) |
| Code generation token limit | 4,000 | `feature_implementer.py` (generate) |
| AI temperature (analysis) | 0.3 | `feature_implementer.py` |
| AI temperature (code gen) | 0.2 | `feature_implementer.py` |

---

## Real-World Case Study

### The "Independent Scrollable Columns" Feature

A real user test was performed where the following feature was requested through the app's own AI chat:

> *"Make the editor and the chat independent columns with independent scrolling"*

#### What Happened

1. **Detection** ✅ — The message was correctly identified as a feature request.
2. **Analysis** ✅ — AI produced a plan to split `.main-content` into two independent scrollable panes.
3. **Code Generation** ⚠️ — AI returned modifications for `editor/templates/editor/index.html` only.
4. **Preview & Approval** ✅ — User reviewed the diff and accepted.
5. **Apply** ✅ — File was overwritten.

#### What Broke

The AI wrapped the existing editor and chat sections in new `<div>` elements with classes like `.split-layout`, `.split-pane`, `.split-pane-left`, `.split-pane-right`, and `.split-pane-scroll`.

**However:**
- `static/css/style.css` was **never modified** — no CSS rules were generated for the new classes.
- `static/js/main.js` was **never modified** — no JavaScript was added for the new scroll behavior.
- The original `.main-content { display: flex }` now wraps a single `.split-layout` div instead of the editor + chat panes directly.

**Result:** The layout broke — editor and chat stacked vertically, scroll behavior lost, the entire UI was visually broken.

#### Root Cause

The `generate_code()` function only received `index.html` as the target file. It had **no awareness** that:
- CSS classes it was creating needed corresponding rules in `style.css`
- The HTML structural changes might affect existing CSS selectors
- JavaScript event listeners might depend on the DOM structure

The AI analyzing the feature likely intended for CSS changes too, but the `files_to_modify` list was either incomplete, or the AI correctly listed multiple files but the code generation for CSS was skipped/failed silently.

---

## Identified Problems

### Problem 1: No Cross-File Context in Code Generation

**Severity: Critical**

The `generate_code()` function receives only ONE file's content at a time. When generating HTML changes, the AI doesn't see the current CSS. When generating CSS changes, the AI doesn't see the HTML it targets.

```python
# Current: each file generated in total isolation
for file_path in files_to_modify[:max_files_to_process]:
    existing_code = feature_implementer.read_file_safely(file_path)
    result = feature_implementer.generate_code(
        feature.description,
        feature.implementation_plan,
        file_path,
        existing_code=existing_code  # ← only THIS file's content
    )
```

**Impact:** CSS classes referenced in HTML don't get defined. JavaScript selectors reference elements that don't exist. Backend API endpoints don't match frontend fetch calls.

### Problem 2: No Validation of Generated Code

**Severity: Critical**

After code is generated, there is **zero validation** before presenting it to the user:
- No syntax checking (HTML/CSS/JS/Python)
- No cross-reference checking (CSS classes used in HTML exist in CSS)
- No import verification (Python imports resolve)
- No selector verification (JS `querySelector` targets exist in HTML)

The user sees a diff but has no way to know if the changes are complete and consistent across files.

### Problem 3: Files Generated in Arbitrary Order

**Severity: High**

The `files_to_modify` list order is whatever the AI returns, and each file is generated independently. This means:
- HTML might be generated first, introducing new CSS classes
- CSS file might be generated second, but without knowing what classes the HTML generation actually created
- Or worse — CSS might not be in the list at all

There's no dependency-aware ordering (e.g., "generate HTML first, then feed its new classes into CSS generation").

### Problem 4: Incomplete `files_to_modify` Lists

**Severity: High**

The `analyze_feature_request()` prompt asks the AI to pick from existing files, but:
- There's no enforcement that the returned list is complete
- The analysis prompt has `max_completion_tokens: 1000`, which may truncate complex plans
- There's no validation that a UI feature includes both template AND style files
- There's no heuristic like: *"if HTML is in the list, CSS should be too"*

### Problem 5: Token Limits Too Low for Large Files

**Severity: Medium**

`generate_code()` has `max_completion_tokens: 4000`. The `style.css` file alone is 937 lines. `views.py` is 961 lines. When the AI must return the **complete file content** (which is how the prompt is structured), 4000 tokens may be insufficient for large files, leading to:
- Truncated output
- JSON parse failures
- Silently incomplete files

### Problem 6: No Iterative Self-Repair

**Severity: Medium**

If the generated code has issues (missing CSS, broken syntax, incomplete files), the pipeline has no mechanism to:
- Detect the problem automatically
- Re-run generation with error feedback
- Ask the AI to fix what it missed

The test_fixer module exists for test failures, but there's no equivalent "feature fixer" that validates generated features work correctly.

---

## Proposed Improvements

### Solution Matrix

| # | Problem | Solution | Effort | Impact |
|---|---------|----------|--------|--------|
| 1 | No cross-file context | Pass related files as read-only context to each generation call | Medium | 🔴 Critical |
| 2 | No validation | Add post-generation validators (syntax, cross-ref, selectors) | Medium | 🔴 Critical |
| 3 | Arbitrary file order | Order files by dependency: HTML → CSS → JS → Python | Low | 🟡 High |
| 4 | Incomplete file lists | Add heuristic rules + AI re-check step | Low | 🟡 High |
| 5 | Token limits too low | Dynamic token limits based on file size; or use diff-only mode | Low | 🟠 Medium |
| 6 | No self-repair | Add validate → fix loop (max 3 iterations) | High | 🟠 Medium |

### Detailed Solutions

#### Solution 1: Cross-File Context Injection

Instead of sending only the target file, include **read-only context** of related files:

```python
def generate_code_with_context(self, feature_description, plan, target_file,
                                existing_code=None, related_files=None):
    """
    Generate code for a target file WITH awareness of related files.
    
    related_files: dict of {filepath: content} for read-only reference
    """
    context_section = ""
    if related_files:
        context_section = "\n\nRELATED FILES (read-only, for reference):\n"
        for path, content in related_files.items():
            context_section += f"\n--- {path} ---\n{content}\n"
    
    prompt = f"""...
    Target File: {target_file}
    {existing_code_section}
    {context_section}
    
    IMPORTANT: Your changes to {target_file} must be consistent with the 
    related files shown above. If you add CSS classes in HTML, those classes 
    must already exist in the CSS file OR you must note them as required.
    ..."""
```

**In the orchestration loop (`implement_feature`):**
```python
# Build context map of all files being modified
all_file_contents = {}
for file_path in files_to_modify:
    info = feature_implementer.read_file_safely(file_path)
    if info['exists'] and info['content']:
        all_file_contents[file_path] = info['content']

# Generate each file with cross-references
for file_path in files_to_modify:
    related = {k: v for k, v in all_file_contents.items() if k != file_path}
    result = feature_implementer.generate_code_with_context(
        feature.description, feature.implementation_plan,
        file_path, existing_code=all_file_contents.get(file_path),
        related_files=related
    )
    # Update context with generated code so next file sees it
    if result.get('success'):
        all_file_contents[file_path] = result['code']
```

#### Solution 2: Post-Generation Validators

```python
class CodeValidator:
    """Validates generated code for consistency and correctness."""
    
    def validate_html_css_consistency(self, html_content, css_content):
        """Check that CSS classes used in HTML are defined in CSS."""
        import re
        # Extract classes from HTML
        html_classes = set(re.findall(r'class="([^"]*)"', html_content))
        html_classes = {c for cls in html_classes for c in cls.split()}
        
        # Extract classes defined in CSS
        css_classes = set(re.findall(r'\.([a-zA-Z_-][\w-]*)', css_content))
        
        # Find missing definitions
        missing = html_classes - css_classes
        return {
            'valid': len(missing) == 0,
            'missing_css_classes': list(missing),
            'message': f"Missing CSS for: {', '.join(missing)}" if missing else "OK"
        }
    
    def validate_js_selectors(self, js_content, html_content):
        """Check that JS selectors target elements that exist in HTML."""
        import re
        selectors = re.findall(r'getElementById\([\'"](\w+)[\'"]\)', js_content)
        selectors += re.findall(r'querySelector\([\'"]#(\w+)[\'"]\)', js_content)
        
        missing = [s for s in selectors if f'id="{s}"' not in html_content]
        return {
            'valid': len(missing) == 0,
            'missing_elements': missing
        }
    
    def validate_python_syntax(self, code):
        """Check Python code compiles without syntax errors."""
        try:
            compile(code, '<generated>', 'exec')
            return {'valid': True}
        except SyntaxError as e:
            return {'valid': False, 'error': str(e), 'line': e.lineno}
```

#### Solution 3: Dependency-Aware File Ordering

```python
FILE_TYPE_PRIORITY = {
    '.html': 1,   # Structure first
    '.css': 2,    # Styling second (references HTML classes)
    '.js': 3,     # Behavior third (references HTML elements + CSS)
    '.py': 4,     # Backend last (API endpoints to match frontend)
}

def order_files_by_dependency(files_to_modify):
    """Sort files so that dependencies flow naturally."""
    def sort_key(filepath):
        ext = os.path.splitext(filepath)[1]
        return FILE_TYPE_PRIORITY.get(ext, 99)
    return sorted(files_to_modify, key=sort_key)
```

#### Solution 4: Smart File List Completion

```python
def ensure_complete_file_list(files_to_modify):
    """
    Heuristic: if a template file is being modified, 
    ensure corresponding CSS and JS files are also included.
    """
    has_template = any('.html' in f for f in files_to_modify)
    has_css = any('.css' in f for f in files_to_modify)
    has_js = any('.js' in f for f in files_to_modify)
    
    if has_template and not has_css:
        files_to_modify.append('static/css/style.css')
    if has_template and not has_js:
        files_to_modify.append('static/js/main.js')
    
    return files_to_modify
```

#### Solution 5: Dynamic Token Limits

```python
def calculate_token_limit(existing_code, base_limit=4000):
    """Scale token limit based on file size."""
    if not existing_code:
        return base_limit
    
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = len(existing_code) // 4
    # Need at least the existing code size + 50% for modifications
    needed = int(estimated_tokens * 1.5)
    return max(base_limit, min(needed, 16000))  # cap at 16k
```

#### Solution 6: Validate-and-Fix Loop

```python
def implement_feature_with_validation(self, feature, files_to_modify, max_iterations=3):
    """Generate code, validate, and auto-fix in a loop."""
    
    for iteration in range(max_iterations):
        generated_files = self.generate_all_files(feature, files_to_modify)
        
        # Run validators
        issues = self.validate_generated_code(generated_files)
        
        if not issues:
            return generated_files  # All good!
        
        if iteration < max_iterations - 1:
            # Feed issues back to AI for repair
            for issue in issues:
                repair_result = self.repair_generated_code(
                    feature, generated_files, issue
                )
                if repair_result.get('success'):
                    generated_files = repair_result['files']
    
    # Return best effort with warnings
    return generated_files, issues
```

---

## Target Architecture

### Current vs. Proposed Pipeline

```
CURRENT (broken for multi-file features):

  analyze → [file1] → generate(file1) → [file2] → generate(file2) → preview → apply
                ↑ no context                ↑ no context
                ↑ no validation             ↑ no validation


PROPOSED (context-aware with validation loop):

  ┌──────────────────────────────────────────────────────────────────────┐
  │                                                                      │
  │  ┌─────────┐     ┌─────────────────┐     ┌──────────────────────┐   │
  │  │ ANALYZE │────▶│ COMPLETE FILE   │────▶│ ORDER BY DEPENDENCY  │   │
  │  │ request │     │ LIST (heuristic)│     │ HTML → CSS → JS → PY │   │
  │  └─────────┘     └─────────────────┘     └──────────┬───────────┘   │
  │                                                      │               │
  │                                                      ▼               │
  │                    ┌────────────────────────────────────────────┐    │
  │                    │  GENERATE CODE (with cross-file context)   │    │
  │                    │                                            │    │
  │                    │  for file in ordered_files:                │    │
  │                    │    related = all other files (originals    │    │
  │                    │              + already-generated)          │    │
  │                    │    code = generate(file, context=related)  │    │
  │                    │    update context with new code            │    │
  │                    │                                            │    │
  │                    └──────────────────┬─────────────────────────┘    │
  │                                       │                              │
  │                                       ▼                              │
  │                    ┌────────────────────────────────────────────┐    │
  │                    │  VALIDATE                                  │    │
  │                    │   • HTML↔CSS class cross-reference         │    │
  │                    │   • JS selector ↔ HTML id/class match      │    │
  │                    │   • Python syntax check                    │    │
  │                    │   • Import resolution                      │    │
  │                    └──────────────────┬─────────────────────────┘    │
  │                                       │                              │
  │                              ┌────────┴────────┐                     │
  │                              │                  │                     │
  │                         issues found       no issues                 │
  │                              │                  │                     │
  │                              ▼                  ▼                     │
  │                    ┌──────────────┐    ┌───────────────┐             │
  │                    │  AI REPAIR   │    │  PREVIEW +    │             │
  │                    │  (feed errors│    │  DIFF (user)  │             │
  │                    │   back to AI)│    └───────┬───────┘             │
  │                    └──────┬───────┘            │                     │
  │                           │                    │                     │
  │                    ┌──────┴──────┐             ▼                     │
  │                    │ iteration   │    ┌───────────────┐              │
  │                    │ < max? ─────┼───▶│    APPLY      │              │
  │                    │    ↑ yes    │    │  + GIT COMMIT  │              │
  │                    │    │        │    └───────────────┘              │
  │                    │  re-validate│                                    │
  │                    └─────────────┘                                    │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Context Flows Forward** — Each generated file updates a shared context map so the next file sees what was already generated.
2. **Structure Before Style** — HTML/templates are generated first, then CSS and JS, so styling/behavior can reference the actual structure.
3. **Validate Before Presenting** — Automated checks catch obvious inconsistencies before the user ever sees a diff.
4. **Self-Healing Loop** — When validation fails, feed the errors back to the AI (up to 3 times) to auto-repair before asking the user.
5. **Dynamic Scaling** — Token limits, context windows, and processing caps scale with the complexity of the target files.

---

## Implementation Roadmap

### Phase 6A — Quick Wins (Low Effort, High Impact)

**Estimated time: 1-2 days**

1. **Heuristic file list completion** — If `.html` is in `files_to_modify`, auto-add `style.css` and `main.js` if not already present.
2. **Dependency-aware file ordering** — Sort `files_to_modify` by type: HTML → CSS → JS → Python.
3. **Dynamic token limits** — Scale `max_completion_tokens` based on existing file size.

### Phase 6B — Cross-File Context (Medium Effort, Critical Impact)

**Estimated time: 3-5 days**

4. **Cross-file context injection** — Pass related file contents as read-only context in every `generate_code()` call.
5. **Progressive context updates** — After generating each file, update the shared context so subsequent files see the latest code.
6. **Enhanced analysis prompt** — Ask the AI to explicitly state cross-file dependencies in its plan.

### Phase 6C — Validation & Self-Repair (Higher Effort, Medium Impact)

**Estimated time: 5-7 days**

7. **CodeValidator class** — HTML↔CSS class checker, JS↔HTML selector checker, Python syntax checker.
8. **Validate-and-fix loop** — Automatically re-run generation with error feedback (max 3 iterations).
9. **Validation report in UI** — Show users a "consistency check" result alongside the diff preview.

---

## Deep Dive: How Code Is Actually Developed Right Now

### Step-by-Step Trace of a Real Feature Request

Let's trace exactly what happens when a user types *"Make the editor and chat independent columns with independent scrolling"* into the chat.

---

#### Step 1: Chat Message Arrives → `views.py` `chat()` (line 143)

The frontend sends a POST to `/api/chat/` with:
```json
{"message": "Make the editor and chat independent columns with independent scrolling"}
```

The view calls `_is_feature_request(message)` (line 225) which does **simple substring matching** against 16 hardcoded patterns:

```python
feature_patterns = [
    'add feature', 'add a feature', 'add the feature',
    'add a ', 'add an ', 'add some',
    'implement', 'create a', 'create an',
    'build a', 'build an',
    'can you add', 'could you add',
    'can you create', 'could you create',
    'can you implement', 'could you implement',
    'want to add', 'need to add',
    'would like to add', 'would like a',
    'i want', 'i need'
]
```

This message does NOT match any pattern (no "add", "implement", "create", "build", "want", "need"). It would only be detected if the user said "Can you **add** independent columns" or "**Implement** independent scrolling". The detection is fragile — many natural phrasings slip through.

**When it IS detected:** A `FeatureRequest` row is created in the database with `status='pending'` and the message as `description`. The feature ID is returned to the frontend.

---

#### Step 2: Frontend Triggers Analysis → `views.py` `analyze_feature()` (line 375)

The frontend sends POST to `/api/analyze-feature/` with `{"feature_id": 42}`.

This calls `feature_implementer.analyze_feature_request(feature.description)` which does two things:

**2a. Scan Project Structure** — `scan_project_structure()` walks the filesystem:
```python
for root, dirs, files in os.walk(self.base_path):
    dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'migrations', '.git']]
    for file in files:
        # Categorize into: python_files, templates, static_files, models, views, urls
```

This produces a flat list of filenames. **No file content is read.** Just names.

**2b. Send to OpenAI API** — Here's the EXACT prompt sent:

```
System: "You are an expert software architect analyzing feature requests.
         Respond with valid JSON only."

User: "Analyze the following feature request for a Django web application:

Feature Request: Make the editor and chat independent columns with
                 independent scrolling

Current Project Structure:
- Django backend (Python)
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Database: SQLite with Django ORM

Existing Files:
Python Files: editor/__init__.py, editor/admin.py, editor/ai_service.py,
              editor/views.py, editor/models.py, ...
Templates: editor/templates/editor/index.html
Static Files: static/css/style.css, static/js/main.js

Existing models: ChatMessage, CodeSnippet, FeatureRequest, CodeExecution
Existing features: Code editor, AI chatbot, Code execution (Python/JS)

IMPORTANT: Use ONLY the actual file paths listed above.

Please provide:
1. Feasibility assessment
2. Implementation plan (step-by-step)
3. List of EXISTING files that need modification
4. Estimated complexity

Respond in JSON format:
{
    "feasible": true/false,
    "plan": ["step 1", "step 2", ...],
    "files_to_modify": ["actual/file/path.py"],
    "estimated_complexity": "simple|medium|complex",
    "reason": "explanation if not feasible"
}"
```

**API parameters:**
| Parameter | Value |
|-----------|-------|
| model | `gpt-5.2` (from env var) |
| temperature | 0.3 |
| max_completion_tokens | **1,000** |
| response_format | `{"type": "json_object"}` |

**What comes back** (example):
```json
{
  "feasible": true,
  "plan": [
    "Modify index.html to wrap editor and chat in flex containers",
    "Add CSS for independent column layout with overflow-y scroll",
    "Optionally add JS for resize handles"
  ],
  "files_to_modify": [
    "editor/templates/editor/index.html",
    "static/css/style.css"
  ],
  "estimated_complexity": "simple"
}
```

**Critical observation:** The AI *might* return `style.css` in the list, or it might not. There's no enforcement. With only 1,000 tokens for the entire analysis response, complex plans can get truncated.

The entire analysis JSON is stored as `feature.implementation_plan` in the database.

---

#### Step 3: Frontend Triggers Implementation → `views.py` `implement_feature()` (line 446)

POST to `/api/implement-feature/` with `{"feature_id": 42}`.

The view parses `files_to_modify` from the stored plan, then **loops through each file independently:**

```python
max_files_to_process = 5
for file_path in files_to_modify[:max_files_to_process]:
    # 1. Read the existing file
    file_info = feature_implementer.read_file_safely(file_path)
    existing_code = file_info['content'] if file_info['exists'] else None
    
    # 2. Generate new code for THIS file alone
    result = feature_implementer.generate_code(
        feature.description,        # "Make the editor and chat..."
        feature.implementation_plan, # The full JSON plan
        file_path,                   # "editor/templates/editor/index.html"
        existing_code=existing_code  # The current file content
    )
```

---

#### Step 4: What Exactly Is Sent to OpenAI for Code Generation

For EACH file, a **separate API call** is made. Here's the exact prompt for `index.html`:

```
System: "You are an expert Django developer generating production-ready code.
         CRITICAL: Return ONLY valid JSON with raw code strings.
         Do NOT wrap code in markdown code blocks.
         The 'code' field must contain raw, unformatted code."

User: "Generate code for this Django application feature:

Feature: Make the editor and chat independent columns with independent scrolling

Implementation Plan: {"feasible": true, "plan": [...], "files_to_modify": [...]}

Target File: editor/templates/editor/index.html
Mode: modify

Current File Content:
[... entire index.html content, all 146 lines ...]

IMPORTANT: Modify the existing code above to add the requested feature.
- Preserve all existing functionality
- Maintain existing imports, functions, and structure
- Only add/modify what's necessary for the new feature

Generate the complete modified file content for editor/templates/editor/index.html.

Respond in JSON format:
{
    "code": "complete file content as raw string",
    "changes_made": ["list of key changes"],
    "notes": "important implementation notes",
    "preserved": ["list of things preserved from original"]
}"
```

**API parameters:**
| Parameter | Value |
|-----------|-------|
| model | `gpt-5.2` |
| temperature | 0.2 |
| max_completion_tokens | **4,000** |
| response_format | `{"type": "json_object"}` |

**What's NOT in this prompt:**
- ❌ The content of `style.css` (937 lines of CSS)
- ❌ The content of `main.js` (607 lines of JS)
- ❌ What CSS classes already exist
- ❌ What JavaScript selectors are in use
- ❌ What the other files in `files_to_modify` are generating

Then if `style.css` IS in the list, a second API call is made — but it also doesn't see what HTML changes were just generated. It only sees the original `style.css` content.

---

#### Step 5: How Modifications Are Inserted

The generated code comes back as a complete file replacement:

```json
{
  "code": "<!DOCTYPE html>\n<html>... entire new file content ...",
  "changes_made": ["Wrapped editor and chat in .split-layout div", "Added .split-pane wrappers"],
  "notes": "CSS for .split-layout needs to be added to style.css"
}
```

Note the irony: the AI's own `notes` field says *"CSS needs to be added to style.css"* — but nothing in the pipeline reads or acts on this note.

The code goes through one cleanup step — stripping markdown backticks if the AI ignored the formatting rules:

```python
if code.startswith('```'):
    first_newline = code.find('\n')
    code = code[first_newline + 1:]
if code.endswith('```'):
    code = code[:-3]
```

Then all generated files are stored in the database as `feature.generated_code` (JSON array) and returned to the frontend for preview.

---

#### Step 6: User Approval → `apply_feature()` in views.py

When the user clicks "Accept", the frontend calls `/api/apply-feature/`. For each file:

```python
# 1. Create backup: style.css → style.css.backup
# 2. Overwrite the file entirely with the generated content
with open(full_path, 'w') as f:
    f.write(content)
```

**This is a full file replacement**, not a surgical edit. The entire file is overwritten with whatever the AI generated. If the AI's 4,000-token response was truncated, the file gets truncated.

---

### Summary: The Data Flow

```
User message
    │
    ▼
[16 substring patterns] ──→ is it a feature? (fragile)
    │
    ▼
[os.walk filesystem]  ──→ file NAMES only (no content)
    │
    ▼
[OpenAI API call #1]  ──→ analysis + files_to_modify list
  ↑ sends: file names, feature text
  ↑ tokens: 1,000 max
  ↑ temp: 0.3
    │
    ▼
FOR EACH file in list (max 5):
    │
    ├─→ [read file from disk] ──→ existing content
    │
    ├─→ [OpenAI API call #N]  ──→ complete new file
    │     ↑ sends: feature text + plan + ONE file's content
    │     ↑ tokens: 4,000 max
    │     ↑ sees: NOTHING about other files
    │
    └─→ store generated code in DB
    │
    ▼
[Show diff to user] ──→ Accept/Reject
    │
    ▼
[Overwrite entire file] ──→ backup original → write new
```

**Total API calls per feature: 1 (analysis) + N (one per file)**
**Total context shared between files: ZERO**

---

## Why It Works Worse Than GitHub Copilot, Claude Code, and Codex

### Comparison Table

| Capability | Your Agent | GitHub Copilot (Agent Mode) | Claude Code | OpenAI Codex CLI |
|------------|-----------|---------------------------|-------------|-----------------|
| **Context window** | 1 file at a time | Entire workspace indexed | Entire workspace indexed | Entire repo in context |
| **File discovery** | AI guesses from filenames | LSP + semantic search | `find`, `grep`, `cat` tools | `bash`, `grep`, file reads |
| **Edit granularity** | Full file replacement | Surgical line edits | Surgical line edits | Surgical line edits |
| **Cross-file awareness** | None | Full (reads related files before editing) | Full (reads imports, references) | Full (runs tools to explore) |
| **Validation** | None | Runs linters, type-checkers | Runs tests, checks syntax | Runs tests in sandbox |
| **Self-repair loop** | None | Re-reads errors, tries again | Re-reads errors, tries again (up to N) | Runs tests → fixes → re-runs |
| **Tool use** | Only OpenAI chat completion | File read/write, terminal, LSP | bash, file I/O, grep, web search | bash, file I/O, full sandbox |
| **Token budget** | 4,000 per file | 128K+ context window | 200K context window | Full model context |
| **Edit format** | AI returns entire file as JSON string | Diff/patch format | `replace_in_file` or `write_file` | Applies patches to files |

### The 7 Fundamental Gaps

#### Gap 1: No Tool Use — Your Agent Is "Blind"

Copilot, Claude Code, and Codex are **agentic** — they have tools. They can:
- Read any file they want (`cat`, `read_file`)
- Search the codebase (`grep`, `ripgrep`, `semantic_search`)
- Run commands (`npm test`, `python manage.py test`)
- Check results and iterate

Your agent gets ONE shot. It receives a prompt, returns JSON, and that's it. It cannot explore. It cannot verify. It cannot say "wait, let me also check what CSS classes exist before I add new HTML classes."

#### Gap 2: Full File Replacement vs. Surgical Edits

Your agent returns the **entire file** as a JSON string value. For a 937-line CSS file, that's ~25,000 characters packed into a JSON `"code"` field. Problems:
- The 4,000-token limit can't even hold the existing file, let alone modifications
- Any small JSON escaping error corrupts the entire file
- The AI must reproduce 900+ lines of unchanged code perfectly to change 10 lines

Copilot and Claude Code use **surgical edits** — they specify "replace lines 108-112 with these 15 new lines." They never touch the other 925 lines.

#### Gap 3: No Iterative Loop

Professional coding agents work in a **loop**:
```
plan → edit → run tests → read errors → fix → run tests → ... → done
```

Your agent works in a **single shot**:
```
plan → generate all files → show to user → done
```

There's no step where it runs the code, sees "`.split-layout` is not styled," and goes back to add the CSS.

#### Gap 4: Context Isolation Between Files

When Copilot edits `index.html`, it first reads `style.css` and `main.js` to understand the existing patterns. It sees that `.main-content` uses `display: flex` and adapts accordingly.

Your agent generates `index.html` changes in a vacuum. It invents CSS class names without knowing what classes already exist. Then when it generates `style.css` (if it even does), it doesn't know what class names the HTML generation actually used.

#### Gap 5: No Semantic Understanding of the Codebase

Your agent receives a flat list of filenames:
```
Python Files: editor/views.py, editor/models.py, ...
Templates: editor/templates/editor/index.html
Static Files: static/css/style.css, static/js/main.js
```

It has NO idea:
- What functions are in `views.py`
- What models exist in `models.py`
- What CSS selectors are defined in `style.css`
- What DOM elements `main.js` manipulates

Copilot and Codex can **read these files** before deciding what to change.

#### Gap 6: Low Token Limits Cause Truncation

| Operation | Your Limit | What's Needed |
|-----------|-----------|---------------|
| Analysis | 1,000 tokens | Fine for simple features, truncates complex plans |
| Code gen for `style.css` (937 lines) | 4,000 tokens | ~8,000-10,000 tokens minimum to return the full file |
| Code gen for `views.py` (961 lines) | 4,000 tokens | ~10,000-12,000 tokens minimum |
| Code gen for `main.js` (607 lines) | 4,000 tokens | ~6,000-8,000 tokens minimum |

At 4,000 tokens, the AI physically cannot return `style.css` in its entirety. It will either truncate or refuse.

#### Gap 7: No AGENTS.md / System Instructions for Your Codebase

Codex supports `AGENTS.md` — a file in your repo root that tells the AI agent about your project conventions, file structure, and rules. Claude Code learns from `.claude/instructions`. Copilot reads `CONTRIBUTING.md`.

Your agent's system prompt is generic: *"You are an expert Django developer."* It doesn't know your specific conventions, your CSS naming scheme, or that `style.css` and `index.html` must always be modified together.

---

## Can You Install Codex and Delegate Implementation to It?

### Short Answer: YES — and this is probably your best path forward.

### How OpenAI Codex CLI Works

Codex CLI is an **open-source** (Apache-2.0) coding agent that runs locally. It's written in Rust and uses the OpenAI API under the hood, but it has a full **agentic loop** with tools — file I/O, bash execution, grep, and a sandboxed environment.

Install:
```bash
npm install -g @openai/codex
# or
brew install --cask codex
```

### Non-Interactive Mode: `codex exec`

This is the key. Codex has a **non-interactive mode** designed exactly for programmatic use:

```bash
codex exec --full-auto "Implement independent scrollable columns for the editor and chat panes"
```

- `--full-auto` — gives it permission to edit files without asking
- `--json` — streams structured JSON events you can parse
- `--output-schema ./schema.json` — forces structured output
- `-o ./result.json` — writes the final message to a file
- `--sandbox workspace-write` — allows file writes but constrains scope

### The Codex SDK (TypeScript)

Even better, there's a **TypeScript SDK** for programmatic control:

```typescript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread();

// Step 1: Analyze
const analysis = await thread.run(
  "Analyze this feature request and list all files that need changes: " + featureDescription
);

// Step 2: Implement
const result = await thread.run(
  "Now implement the changes. Modify all necessary files."
);
```

### Architecture: Your Agent as Orchestrator, Codex as Implementer

```
┌─────────────────────────────────────────────────────────────────────┐
│  YOUR DJANGO APP (orchestrator)                                     │
│                                                                     │
│  User message                                                       │
│      │                                                              │
│      ▼                                                              │
│  [Feature Detection] ──→ is it a feature?                           │
│      │                                                              │
│      ▼                                                              │
│  [Build Prompt] ──→ combine user request + project conventions      │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  CODEX (the actual implementer)                              │   │
│  │                                                              │   │
│  │  subprocess.run([                                            │   │
│  │    'codex', 'exec', '--full-auto',                           │   │
│  │    '--sandbox', 'workspace-write',                           │   │
│  │    '--json',                                                 │   │
│  │    '-o', '/tmp/result.json',                                 │   │
│  │    prompt                                                    │   │
│  │  ], cwd=project_dir)                                         │   │
│  │                                                              │   │
│  │  Codex internally:                                           │   │
│  │   • reads all relevant files                                 │   │
│  │   • plans the changes                                        │   │
│  │   • makes surgical edits to each file                        │   │
│  │   • runs tests to verify                                     │   │
│  │   • fixes issues if tests fail                               │   │
│  │   • repeats until done                                       │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  [Git Diff] ──→ capture what Codex changed                          │
│      │                                                              │
│      ▼                                                              │
│  [Show Preview to User] ──→ Accept / Reject                        │
│      │                                                              │
│      ▼                                                              │
│  [Git Commit or Rollback]                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Integration Code Sketch (Python)

```python
import subprocess
import json
import os

class CodexImplementer:
    """Delegates feature implementation to OpenAI Codex CLI."""
    
    def __init__(self, project_dir: str, api_key: str):
        self.project_dir = project_dir
        self.api_key = api_key
    
    def implement_feature(self, description: str, plan: str = None) -> dict:
        """
        Run Codex in non-interactive mode to implement a feature.
        
        Returns dict with:
          - success: bool
          - files_changed: list of file paths
          - summary: str
        """
        prompt = self._build_prompt(description, plan)
        
        env = os.environ.copy()
        env['CODEX_API_KEY'] = self.api_key
        
        result = subprocess.run(
            [
                'codex', 'exec',
                '--full-auto',
                '--sandbox', 'workspace-write',
                '--json',
                prompt
            ],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            env=env,
            timeout=300  # 5 minute timeout
        )
        
        # Parse JSON Lines output
        events = []
        for line in result.stdout.strip().split('\n'):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        
        # Extract file changes from events
        file_changes = [
            e['item'] for e in events 
            if e.get('type') == 'item.completed' 
            and e.get('item', {}).get('type') == 'file_change'
        ]
        
        # Get final message
        final_messages = [
            e['item']['text'] for e in events
            if e.get('type') == 'item.completed'
            and e.get('item', {}).get('type') == 'agent_message'
        ]
        
        return {
            'success': result.returncode == 0,
            'files_changed': file_changes,
            'summary': final_messages[-1] if final_messages else '',
            'all_events': events
        }
    
    def _build_prompt(self, description: str, plan: str = None) -> str:
        prompt = f"""Implement the following feature in this Django web application:

Feature: {description}

Rules:
- This is a Django app with vanilla HTML/CSS/JS frontend
- The main template is editor/templates/editor/index.html
- Styles are in static/css/style.css
- JavaScript is in static/js/main.js
- Always modify ALL necessary files (HTML, CSS, JS, Python)
- Preserve all existing functionality
- Test your changes work correctly
"""
        if plan:
            prompt += f"\nImplementation plan:\n{plan}"
        
        return prompt
```

### What You'd Replace

| Current Code | Replaced By |
|-------------|-------------|
| `feature_implementer.analyze_feature_request()` | Keep it (or let Codex analyze too) |
| `feature_implementer.generate_code()` — per-file loop | `codex exec` — single call handles all files |
| `feature_implementer.apply_changes()` — per-file write | Codex writes files directly; you just review the git diff |
| No validation | Codex runs tests internally |
| No cross-file context | Codex reads all files it needs |

### Authentication Options

| Method | Setup | Cost |
|--------|-------|------|
| ChatGPT sign-in | `codex` then "Sign in with ChatGPT" | Included in Plus/Pro/Team plans |
| API key | Set `CODEX_API_KEY` env var | Pay-per-token via OpenAI API |

For a server deployment, you'd use the API key method:
```bash
export CODEX_API_KEY=sk-...
codex exec --full-auto "implement the feature"
```

### Alternative: Claude Code (Anthropic)

Claude Code (`claude` CLI) is another option with similar capabilities:
- Also runs locally
- Has a `-p` flag for non-interactive/piped mode  
- Can read/write files, run commands, search code
- Uses the Anthropic API (requires `ANTHROPIC_API_KEY`)
- 200K context window

You could even support **both** and let the user choose their backend agent.

### Recommendation

The fastest path to dramatically better feature development:

1. **Keep your existing detection + analysis** — they work fine for identifying and planning features
2. **Replace `generate_code()` with `codex exec`** — delegate the actual file editing to a real coding agent
3. **Capture the git diff** after Codex runs — show it in your existing preview UI
4. **Keep your approval workflow** — user still reviews and accepts/rejects
5. **Keep your git integration** — commit on approve, rollback on reject

This turns your app from a "single-shot code generator" into an "orchestrator that delegates to a professional coding agent" — which is exactly how production AI coding tools work.

---

*Document generated from analysis of the Self-Building App codebase, February 2026.*
*Based on real-world testing of the feature implementation pipeline.*
