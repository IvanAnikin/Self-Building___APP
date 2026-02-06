# Self-Building App 🚀

A modern Python Django web application featuring a dark mode code editor with an integrated AI chatbot assistant. The chatbot allows users to request new features, which will be developed and integrated into the application in real-time.

## Features

✨ **Dark Mode UI** - Beautiful, modern dark theme interface  
📝 **Code Editor** - Full-featured text editor (2/3 of screen width)  
🤖 **AI Assistant Chatbot** - Interactive AI-powered chatbot with context awareness  
💬 **Conversation History** - Chat messages are saved and used for context  
💾 **Save Functionality** - Save your code snippets to database  
🗄️ **Feature Request Tracking** - Automatic detection and tracking of feature requests  
▶️ **Run Button** - Execute your code (placeholder for future implementation)  
🎨 **Responsive Design** - Works on desktop and tablet devices  
🌐 **Multi-language Support** - English, Czech, Japanese, and Russian translations  

## Screenshots

### Main Interface
![Self-Building App Interface](https://github.com/user-attachments/assets/2c2fbf06-489f-4b93-afac-e077ad626638)

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
- Use the **Run** button to execute code (coming soon)
- Tab key inserts 4 spaces for proper code indentation

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
Tracks feature requests made by users and their implementation status.

## API Endpoints

- `GET /` - Main application interface
- `POST /api/chat/` - Send message to AI assistant
  - Request: `{ "message": "your message", "code_context": "optional code" }`
  - Response: `{ "status": "success", "response": "AI response", "ai_enabled": true/false }`
- `POST /api/save/` - Save code snippet
  - Request: `{ "code": "your code", "filename": "filename.py" }`
  - Response: `{ "status": "success", "message": "Code saved", "snippet_id": 1 }`

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

⏳ **Phase 3: Code Execution** (Next)
- Sandboxed Python execution environment
- Real-time output display
- Multiple language support
- Error handling and debugging

⏳ **Phase 4: Self-Modification**
- AI-powered code generation
- Automated file modification
- Feature implementation from natural language
- Version control integration

⏳ **Phase 5: Collaboration**
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

**Note**: Phase 2 is complete! The AI-powered chatbot now features:
- ✅ OpenAI API integration with intelligent, context-aware responses
- ✅ Automatic conversation history tracking
- ✅ Code context awareness (AI can see and understand your editor content)
- ✅ Feature request detection and tracking in database
- ✅ Fallback mode that works without an API key
- ✅ Persistent storage for all chat messages and code snippets

The application is fully functional without an API key using smart fallback responses. Add an OpenAI API key to unlock the full AI capabilities!
