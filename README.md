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
🚀 **AI Feature Implementation** - Request features in natural language and get implementation previews  
🔧 **Code Generation** - AI-powered code generation for requested features  
📋 **Implementation Plans** - Detailed feasibility analysis and implementation strategies  
🎨 **Responsive Design** - Works on desktop and tablet devices  
🌐 **Internationalization** - English, Czech, Japanese, and Russian translations  

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
- `GET /api/features/` - List all feature requests
  - Response: `{ "status": "success", "features": [...] }`
- `POST /api/features/analyze/` - Analyze feature feasibility (Phase 4)
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "analysis": { "feasible": true, "plan": "...", "complexity": "medium" } }`
- `POST /api/features/implement/` - Generate code for feature (Phase 4)
  - Request: `{ "feature_id": 1 }`
  - Response: `{ "status": "success", "generated_files": [...] }`

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

🚧 **Phase 4: Self-Modification** (In Progress)
- ✅ AI-powered feasibility analysis
- ✅ Automated code generation from natural language
- ✅ Feature request detection and tracking
- ✅ Implementation preview system
- ✅ FeatureImplementer service with 7 core methods
- ⏳ User approval workflow for changes
- ⏳ Automated file modification with backup
- ⏳ Version control integration (Git commits)
- ⏳ Automated testing and rollback

⏳ **Phase 5: Collaboration** (Next)
- User authentication and authorization
- Project sharing and permissions
- Real-time collaboration (WebSockets)
- Code review system  

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: Phases 1-3 complete! Phase 4 in progress! The application now features:

**Phase 3 - Code Execution:**
- ✅ Sandboxed code execution for Python and JavaScript
- ✅ Real-time output display in a collapsible panel
- ✅ Comprehensive error handling with full tracebacks
- ✅ Timeout protection (5 seconds) to prevent infinite loops
- ✅ Output truncation for large outputs (10,000 char limit)
- ✅ Execution history tracking in database

**Phase 4 - Self-Modification (In Progress):**
- ✅ AI-powered feature analysis and code generation
- ✅ Feature request detection with "Implement" button
- ✅ FeatureImplementer service with 7 core methods
- ✅ Implementation preview system
- ⏳ User approval workflow and automated application (coming soon)

The application is fully functional for writing, saving, and executing code. Phase 2 AI features work without an API key using smart fallback responses. **Add an OpenAI API key to unlock Phase 4's full self-building capabilities including automated feature implementation!**
