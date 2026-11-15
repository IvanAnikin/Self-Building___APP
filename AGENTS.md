# Self-Building App — Agent Instructions

## Project Overview
This is a Django web application ("Self-Building App") that includes a code editor,
AI chatbot, code execution engine, and AI-powered self-modification capability.

## Tech Stack
- Backend: Django 4.2+ / Python 3.9+
- Frontend: Vanilla HTML, CSS, JavaScript (no framework)
- Database: SQLite via Django ORM
- AI: OpenAI API (GPT models)
- Version Control: Git (per-user branches)

## Project Structure

### Key Files
- `editor/templates/editor/index.html` — Main (and only) HTML template
- `static/css/style.css` — All application styles (~937 lines)
- `static/js/main.js` — All frontend JavaScript (~753 lines)
- `editor/views.py` — All API views and auth views (~961 lines)
- `editor/models.py` — All Django models
- `editor/urls.py` — App-level URL routing
- `selfbuilding_app/urls.py` — Project-level URL routing

### File Relationships
- HTML template uses classes defined in `style.css`
- HTML template references IDs used by `main.js` (querySelector, getElementById)
- `main.js` calls API endpoints defined in `views.py`
- `views.py` uses models from `models.py`

## Critical Rules

### CSS ↔ HTML Consistency
- If you add a CSS class to any HTML element, you MUST define that class in
  `static/css/style.css`.
- If you remove an HTML element, check if its CSS rules should be removed.
- The existing layout uses `display: flex` on `.main-content` (line ~108 of style.css).

### JavaScript ↔ HTML Consistency
- If you add an HTML element with an `id`, check if `main.js` needs to reference it.
- If you change an element's `id`, update all `getElementById()` and `querySelector()`
  calls in `main.js`.

### Django Conventions
- All views use `@login_required` decorator.
- All model queries filter by `user=request.user` for data isolation.
- API views return `JsonResponse` with `{'status': 'success'|'error', ...}`.
- CSRF token is sent via `X-CSRFToken` header from frontend.

### Do NOT Modify
- `editor/codex_service.py` — The Codex integration service itself
- `editor/ai_service.py` — Chat AI service
- `selfbuilding_app/settings.py` — Django settings
- `manage.py`
- Any migration files
- Any `.backup` files

### Testing
- Run `python manage.py test editor` to check Django tests.
- The app runs on `http://127.0.0.1:8000`.

### Code Style
- Python: 4-space indentation, single quotes for strings, docstrings on all functions.
- JavaScript: 4-space indentation, single quotes, `async/await` for API calls.
- CSS: 4-space indentation, BEM-like class naming, all colors use CSS variables
  defined in `:root`.
