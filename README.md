# Self-Building App 🚀

A modern Python Django web application featuring a dark mode code editor with an integrated AI chatbot assistant. The chatbot allows users to request new features, which will be developed and integrated into the application in real-time.

## Features

✨ **Dark Mode UI** - Beautiful, modern dark theme interface  
📝 **Code Editor** - Full-featured text editor (2/3 of screen width)  
🤖 **AI Assistant Chatbot** - Interactive AI-powered chatbot with context awareness  
💬 **Conversation History** - Chat messages are saved and used for context  
💾 **Save Functionality** - Save your code snippets to database  
🗄️ **Feature Request Tracking** - Automatic detection and tracking of feature requests  
▶️ **Code Execution** - Execute Python and JavaScript code with real-time output  
⚡ **Multi-Language Support** - Python 3 and JavaScript (Node.js) execution  
🛡️ **Sandboxed Execution** - Safe code execution with timeout and resource limits  
🚀 **AI Feature Analysis** - Request features in natural language and get feasibility analysis  
🔧 **Code Generation Preview** - AI-powered code generation with implementation preview (doesn't auto-apply yet)  
📋 **Implementation Plans** - Detailed step-by-step implementation strategies  
🎨 **Responsive Design** - Works on desktop and tablet devices  
🌐 **Internationalization** - English, Czech, Japanese, and Russian translations  

## How AI Feature Development Works (Phase 4)

When you request a feature (e.g., "add line numbers to the editor"):

1. **Detection** 🔍 - System automatically detects it's a feature request
2. **Analysis** 🧠 - AI analyzes feasibility, scans project structure, creates implementation plan
3. **Code Generation** 💻 - AI generates context-aware code that preserves existing functionality
4. **Preview** 👁️ - Review the generated changes with side-by-side diff viewer
5. **User Approval** ✅❌ - Accept to apply changes or reject to discard them
6. **Application** 🎯 - Approved changes are safely applied to your files with automatic backups

**New in Phase 4 Part 3:** The application now supports a complete approval workflow! You can review generated code changes in a beautiful diff viewer, then either accept to apply them to your project files or reject to discard them. All file modifications create automatic backups for safety.

## Screenshots

### Main Interface
![Self-Building App Interface](https://github.com/user-attachments/assets/b1a31039-96e3-4657-a0e8-355cc130306c)

### Code Execution - Python
![Python Code Execution](https://github.com/user-attachments/assets/05c356ec-cfee-4e07-9a6e-51322d92f2e3)

### Error Handling
![Error Handling Demo](https://github.com/user-attachments/assets/106c188b-6c08-4fd1-b5e3-24286c9f4d57)

### JavaScript Execution
![JavaScript Support](https://github.com/user-attachments/assets/9a31824f-1c75-4e19-b8a8-16a78004d068)

### Chat Interaction
![Chat Demo](https://github.com/user-attachments/assets/9d9d9b91-f38f-4cb3-a6f0-0e6ca8621d7b)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key (optional, for AI-powered responses)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/IvanAnikin/Self-Building___APP.git
   cd Self-Building___APP
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables (optional for AI features)**
   
   Edit the `.env` file (already included in repository) and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-actual-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```
   
   **Note:** The application works without an API key using fallback responses. To enable AI-powered intelligent responses, you need to:
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Generate an API key from your account dashboard
   - Add the key to your `.env` file

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## Usage

### Code Editor
- Type or paste your code in the left panel (occupies 2/3 of the screen)
- Edit the filename in the input field at the top
- Use the **Save** button to save your code
- Use the **Run** button to execute code (Python and JavaScript supported)
- Tab key inserts 4 spaces for proper code indentation
- View execution output in the collapsible output panel below the editor

### Code Execution
- **Supported Languages**: Python 3 and JavaScript (Node.js)
- Click the **Run** button to execute your code
- Output appears in a dedicated panel below the editor
- Successful execution shows standard output in green
- Errors display full traceback/error messages in red
- Execution has a 5-second timeout to prevent infinite loops
- Output is truncated after 10,000 characters
- Use the **Clear** button to hide the output panel
- All executions are saved to the database for history tracking

### AI Assistant
- The AI chatbot appears on the right side (occupies 1/3 of the screen)
- Type your message or feature request in the text area at the bottom
- Press **Send** or hit Enter to submit your message
- The AI assistant responds with context-aware answers
- **With OpenAI API key**: Get intelligent, context-aware responses powered by GPT-4o-mini
- **Without API key**: Get helpful fallback responses with basic functionality
- The assistant can:
  - Answer coding questions
  - Help debug code issues
  - Acknowledge and track feature requests
  - Provide guidance on implementation
  - Understand the code currently in your editor for better context

### Feature Requests
Users can request features like:
- "Add user authentication"
- "Create a database for saving projects"
- "Add syntax highlighting"
- "Implement code execution"

The chatbot will:
- Acknowledge your request with intelligent responses
- Save feature requests to the database automatically
- Track request status (pending, processing, completed, failed)
- Provide guidance on implementation approaches (when AI is enabled)

## Project Structure

```
Self-Building___APP/
├── editor/                 # Main Django app
│   ├── models.py          # Database models (ChatMessage, CodeSnippet, FeatureRequest)
│   ├── views.py           # View handlers
│   ├── urls.py            # URL routing
│   └── templates/         # HTML templates
│       └── editor/
│           └── index.html # Main application template
├── static/                # Static files
│   ├── css/
│   │   └── style.css     # Dark mode styling
│   └── js/
│       └── main.js       # Frontend JavaScript
├── selfbuilding_app/      # Django project settings
│   ├── settings.py       # Project configuration
│   └── urls.py           # Main URL configuration
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Technology Stack

- **Backend**: Django 4.2+
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI Integration**: OpenAI API (GPT-4o-mini)
- **Database**: SQLite (default, can be configured for PostgreSQL/MySQL)
- **Styling**: Custom CSS with dark mode theme
- **Internationalization**: Django i18n with 4 language translations

## Database Models

### ChatMessage
Stores conversations between users and the AI assistant.

### CodeSnippet
Stores code snippets created in the editor.

### FeatureRequest
Tracks feature requests made by users and their implementation status. Enhanced in Phase 4 with:
- Implementation plans and generated code
- Files modified tracking (JSON)
- Git commit hashes for version control
- Test results and error logs
- Status tracking (pending, processing, approved, rejected, completed, failed)

### CodeExecution
Stores code execution history including code, language, output, errors, and execution status.

## API Endpoints

- `GET /` - Main application interface
- `POST /api/chat/` - Send message to AI assistant
  - Request: `{ "message": "your message", "code_context": "optional code" }`
  - Response: `{ "status": "success", "response": "AI response", "ai_enabled": true/false }`
- `POST /api/save/` - Save code snippet
  - Request: `{ "code": "your code", "filename": "filename.py" }`
  - Response: `{ "status": "success", "message": "Code saved", "snippet_id": 1 }`
- `POST /api/execute/` - Execute code
  - Request: `{ "code": "your code", "language": "python", "filename": "script.py" }`
  - Response: `{ "status": "success/error", "stdout": "output", "stderr": "errors", "returncode": 0, "execution_id": 1 }`
- `GET /api/features/` - List all feature requests ✅
  - Response: `{ "status": "success", "features": [{"id": 1, "description": "...", "status": "approved", "has_plan": true, "has_code": true}] }`
- `POST /api/features/analyze/` - Analyze feature feasibility ✅
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "analysis": { "feasible": true, "plan": ["Step 1: ...", "Step 2: ..."], "files_to_modify": ["editor/templates/editor/index.html"], "estimated_complexity": "simple" } }`
- `POST /api/features/implement/` - Generate code for feature ✅
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "generated_files": [{"file": "editor/templates/editor/index.html", "code": "...", "changes": ["Added line numbers div"], "notes": "..."}], "message": "Code generated successfully" }`
- `POST /api/features/preview/` - Preview changes with diff ✅ **NEW**
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "previews": [{"file": "path/to/file.py", "diff": "unified diff", "additions": 10, "deletions": 2, "file_exists": true}] }`
- `POST /api/features/apply/` - Apply approved changes to files ✅ **NEW**
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "message": "Applied changes to 1 file(s)", "applied_files": [{"file": "path/to/file.py", "backup_created": true}] }`
- `POST /api/features/reject/` - Reject and discard changes ✅ **NEW**
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "message": "Feature changes rejected" }`

## Future Roadmap

✅ **Phase 1: Foundation** (Completed)
- Basic code editor with tab support
- Dark mode UI with responsive design
- Chat interface with message history
- Multi-language support (EN, CS, JA, RU)
- Database models for tracking

✅ **Phase 2: AI Integration** (Completed)
- OpenAI API integration (GPT-4o-mini)
- Context-aware intelligent responses
- Conversation history memory
- Feature request detection and tracking
- Code context awareness
- Graceful fallback mode

✅ **Phase 3: Code Execution** (Completed)
- Sandboxed Python execution environment
- Real-time output display in dedicated panel
- Multiple language support (Python, JavaScript)
- Comprehensive error handling and debugging
- Timeout and resource limits (5 seconds default)
- Output truncation for large outputs
- Execution history tracking in database

✅ **Phase 4: Self-Modification - Complete!** (Completed)
- ✅ Part 1: AI-powered feasibility analysis
- ✅ Part 2: Context-aware code generation from natural language
- ✅ Part 3: User approval workflow with automated file modification ⭐ **NEW!**
- ✅ Feature request detection and tracking
- ✅ Implementation preview system with diff viewer
- ✅ FeatureImplementer service with complete workflow
- ✅ Project structure scanning
- ✅ Safe file reading and code generation
- ✅ Six API endpoints (analyze, implement, list, preview, apply, reject)
- ✅ Automatic backup creation before modifications
- ✅ Accept/Reject workflow with visual diff viewer

✅ **Phase 5: Advanced Features** (Complete!)
- User authentication and authorization
- Version control integration (Git commits)
- Automated testing and rollback mechanism

⏳ **Phase 6: Collaboration** (Optional)
- Project sharing and permissions
- Real-time collaboration (WebSockets)
- Code review system
- Team workspaces

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: Phases 1-4 complete! The application now features:

**Phase 3 - Code Execution:**
- ✅ Sandboxed code execution for Python and JavaScript
- ✅ Real-time output display in a collapsible panel
- ✅ Comprehensive error handling with full tracebacks
- ✅ Timeout protection (5 seconds) to prevent infinite loops
- ✅ Output truncation for large outputs (10,000 char limit)
- ✅ Execution history tracking in database

**Phase 4 - Self-Modification (Fully Complete!):**
- ✅ AI-powered feature analysis and code generation
- ✅ Feature request detection with "Implement" button
- ✅ FeatureImplementer service with complete workflow
- ✅ Implementation preview system with diff viewer ⭐ **NEW!**
- ✅ User approval workflow (Accept/Reject) ⭐ **NEW!**
- ✅ Context-aware code modification
- ✅ Project structure scanning
- ✅ Safe file reading and preservation of existing code
- ✅ Automatic backup creation before applying changes ⭐ **NEW!**
- ✅ Full workflow: Feature Request → Analysis → Code Generation → Preview → **User Approval → Apply to Files** ⭐ **NEW!**

The application is fully functional for writing, saving, executing code, and generating AND APPLYING feature implementations! **Add an OpenAI API key to unlock Phase 4's AI-powered self-building capabilities including intelligent feature analysis, automated code generation, and safe file modification with user approval!**

**Phase 4 Part 3 Complete:** When you request a feature (like "add line numbers"), the AI generates the modified code, shows you a beautiful diff preview in a modal, and you can choose to Accept (apply to files with automatic backup) or Reject (discard changes). Full self-modification capability with safety controls!

**Phase 5 - Multi-User Platform (Complete!):**
- ✅ User authentication system (register/login/logout)
- ✅ Multi-user support with complete data isolation
- ✅ Per-user workspaces (chat history, files, features)
- ✅ Git-based version control (per-user branches)
- ✅ Automated testing framework (pytest/unittest/Django)
- ✅ AI-powered test fixing with retry mechanism
- ✅ Version history tracking and rollback capability
- ✅ Secure user sessions with CSRF protection
- ✅ Beautiful authentication UI with dark theme

**What Phase 5 Enables:**
- Multiple users can use the app simultaneously
- Each user has their own isolated workspace
- Users cannot see or modify each other's data
- Every user builds their own version of the application
- Version control tracks all feature implementations
- Automated testing ensures code quality (integration pending)
- Rollback to any previous version instantly

---

## Future Improvements & Expansion Ideas

### ✅ Completed in Phase 5

#### 1. Multi-User & Authentication System ✅ **COMPLETE**
**Implemented:** User accounts with complete isolation
- ✅ Django authentication (login/register/logout)
- ✅ User-specific code snippets, chat history, and feature requests
- ✅ User profiles with preferences and settings
- ⏳ OAuth integration (GitHub, Google, Microsoft) - Future enhancement
- ⏳ Role-based permissions (admin, developer, viewer) - Future enhancement

#### 2. Version Control Integration ✅ **COMPLETE**
**Implemented:** Git-based version control per user
- ✅ Git integration for tracking changes
- ✅ Per-user branches (user-{id}-workspace)
- ✅ Version history API endpoints
- ✅ Rollback to previous versions
- ✅ Commit tracking with user tags
- ⏳ Visual diff viewer in UI - Ready for implementation
- ⏳ Branch management UI - Ready for implementation

#### 3. Automated Testing Framework ✅ **COMPLETE**
**Implemented:** Testing and rollback system
- ✅ TestRunner service (pytest/unittest/Django support)
- ✅ AI-powered test failure analysis
- ✅ Automatic fix generation
- ✅ TestResult model for tracking
- ⏳ Integration with feature workflow - Ready for implementation
- ⏳ UI for test results - Ready for implementation

### 🎯 Remaining Enhancement Opportunities

#### 2. Modern Code Editor Upgrade
**Current Issue:** Basic textarea lacks professional IDE features
- Replace with **Monaco Editor** (VS Code's editor) or **CodeMirror**
- IntelliSense/autocomplete
- Advanced syntax highlighting for 100+ languages
- Error detection & linting
- Code folding and find/replace
- Multiple themes
- Minimap for code navigation

#### 3. Project/Workspace Management
**Current Issue:** Single file editing only
- Multi-file projects with folder structure
- File tree/explorer sidebar
- Create/delete/rename files and folders
- Project templates (Django, Flask, React, etc.)
- Import/export projects as ZIP
- Recent projects list

### 🚀 High-Impact Feature Additions

#### 4. Version Control Integration
- Git integration for tracking changes
- Visual diff viewer (foundation already exists!)
- Branch management
- Rollback to previous versions
- Change history timeline
- Auto-commit applied changes

#### 5. Real-Time Collaboration
- WebSocket support (Django Channels)
- Multi-user editing (like Google Docs)
- Shared workspaces
- Live cursor positions
- Chat rooms per project
- Screen sharing for pair programming

#### 6. AI Features Enhancement
**Expand AI capabilities beyond chat:**
- **Code Review** - AI analyzes code for bugs, security issues
- **Test Generation** - Auto-generate unit tests
- **Documentation** - Auto-generate docstrings/comments
- **Code Refactoring** - Suggest improvements
- **Bug Detection** - Identify potential issues
- **Code Explanation** - Explain complex code blocks
- **Multiple AI Models** - Support Claude, Gemini, local models

#### 7. Extended Language Support
**Currently:** Python & JavaScript only
**Expand to:** TypeScript, Java, C++, Go, Rust, Ruby, PHP, and more
- Language-specific execution environments
- Syntax validation for each language
- Language-specific AI assistance

### 💼 Business & Market Expansion

#### 8. Target Audience Segments

**A. Education Sector** 📚
- **Student Mode:** Step-by-step tutorials, hints, progress tracking
- **Teacher Dashboard:** Assign coding exercises, auto-grading
- **Classroom Management:** Create student accounts, monitor progress
- **Lesson Plans:** Pre-built curriculum with AI tutor
- **Certificate Generation:** Completion certificates

**B. Enterprise/Teams** 🏢
- **Team Workspaces:** Shared projects, role permissions
- **Code Review Workflow:** Pull request-style approval process
- **Audit Logs:** Track who changed what and when
- **SSO Integration:** SAML, Active Directory
- **Private Deployment:** Self-hosted option for security
- **API Access:** Integrate with existing tools

**C. Content Creators/Bloggers** ✍️
- **Embeddable Code Snippets:** Share live, editable code examples
- **Presentation Mode:** Clean interface for screencasts
- **Export Options:** GIF recordings, screenshots, markdown
- **Tutorial Builder:** Create interactive coding tutorials

**D. Interview/Assessment Platform** 💼
- **Coding Challenges:** Timed problems with test cases
- **Candidate Evaluation:** Track solutions, time spent
- **Video Recording:** Record coding sessions
- **Problem Library:** LeetCode-style question bank
- **Automated Scoring:** Test case validation

### 🎨 UX/UI Improvements

#### 9. Interface Enhancements
- **Responsive Mobile Design** - Currently desktop-only
- **Customizable Layout** - Draggable panels, resizable sections
- **Dark/Light/Custom Themes** - Theme marketplace
- **Keyboard Shortcuts** - Ctrl+S to save, etc.
- **Command Palette** - VS Code-style (Ctrl+Shift+P)
- **Split View** - Compare files side-by-side
- **Breadcrumbs** - Show file path navigation

#### 10. Dashboard & Analytics
- Recent Projects
- Code Execution Stats (runs, success rate)
- AI Usage Metrics (API calls, tokens used)
- Feature Request Timeline
- Popular Code Snippets
- Activity Feed

### 🔧 Technical Improvements

#### 11. Database Upgrade
**Current:** SQLite (single-user, file-based)
**Upgrade to:** PostgreSQL
- Better concurrency for multi-user
- Full-text search capabilities
- Improved scalability for production

#### 12. Caching Layer
- Redis for caching AI responses (expensive API calls)
- Cache code execution results
- Improved session management

#### 13. Container Isolation
**Current:** Direct subprocess execution (security risk)
**Better:** Docker containers per execution
- Isolated execution environment
- Network isolation
- Memory and CPU limits
- Timeout enforcement

#### 14. Testing Infrastructure
Currently missing:
- Unit tests for all modules
- Integration tests for API endpoints
- Frontend tests (Jest/Playwright)
- CI/CD pipeline (GitHub Actions)
- Automated security scanning

### 🌟 Innovative Features

#### 15. AI Agents/Copilots
- **Code Completion Agent** - Real-time suggestions as you type
- **Debug Agent** - Automatically fix errors
- **Optimization Agent** - Improve performance
- **Security Agent** - Scan for vulnerabilities
- **Documentation Agent** - Keep docs in sync

#### 16. Marketplace/Plugin System
- Community plugins (linters, formatters)
- Theme marketplace
- Code snippet libraries
- Template marketplace
- AI prompt templates

#### 17. Code Snippet Sharing
- **Public/Private Snippets** - Like GitHub Gists
- **Social Features** - Like, comment, fork snippets
- **Snippet Discovery** - Search public code examples
- **Embed API** - Embed snippets in external sites

#### 18. Jupyter Notebook Integration
- Support `.ipynb` files
- Cell-based execution
- Inline visualizations
- Data science workflows
- Export to PDF/HTML

### 🎯 Quick Wins (Priority Implementation)

1. **Add Monaco Editor** (1-2 days) - Massive UX improvement
2. **User Authentication** (2-3 days) - Enable multi-user
3. **File Tree System** (3-4 days) - Multi-file projects
4. **Git Integration** (2-3 days) - Already have backups
5. **Redis Caching** (1 day) - Reduce API costs
6. **TypeScript Support** (1 day) - Popular language
7. **Export/Import Projects** (1-2 days) - User retention
8. **Keyboard Shortcuts** (1 day) - Power user feature

### 🌍 Use Cases Matrix

| User Type | Primary Use Case | Key Features Needed |
|-----------|-----------------|---------------------|
| Students | Learn to code | Tutorials, hints, auto-grading |
| Teachers | Teach programming | Classroom mgmt, assignments |
| Developers | Quick prototyping | Git, multiple languages, AI assist |
| Interviewers | Assess candidates | Timed challenges, recording |
| Bloggers | Code examples | Embed API, export options |
| Teams | Collaborate on code | Real-time editing, chat |
| Freelancers | Client demos | Presentation mode, sharing |
| Researchers | AI experiments | Custom models, API access |

### 🔐 Security & Compliance

Add these for enterprise readiness:
- **SOC 2 Compliance** - Security audits
- **GDPR Compliance** - Data privacy (EU)
- **2FA/MFA** - Two-factor authentication
- **Audit Logs** - Complete activity tracking
- **Data Encryption** - At rest and in transit
- **Rate Limiting** - Prevent abuse
- **IP Whitelisting** - Enterprise feature

### 📈 Marketing Positioning Ideas

**Alternative Names:**
- "CodeCraft AI" - AI-Powered Development Environment
- "EvolveLab" - The IDE That Writes Itself
- "Codespace AI" - Collaborative AI Coding Platform
- "DevAssist Pro" - Your AI Development Partner

**Taglines:**
- "Code smarter, not harder"
- "Your AI pair programmer, 24/7"
- "From idea to implementation in minutes"
- "The future of collaborative coding"

### 📊 Potential Monetization Strategy

**Free Tier:**
- 100 AI requests/month
- 50 code executions/day
- 5 projects
- Public snippets only

**Pro ($9/month):**
- Unlimited AI requests
- Unlimited executions
- Unlimited projects
- Private workspaces
- Priority support

**Team ($29/month/5 users):**
- Everything in Pro
- Shared workspaces
- Team collaboration
- Admin dashboard
- SSO integration

**Enterprise (Custom):**
- Self-hosted deployment
- Custom AI models
- SLA guarantees
- Dedicated support