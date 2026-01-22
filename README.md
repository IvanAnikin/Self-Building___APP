# Self-Building App 🚀

A modern Python Django web application featuring a dark mode code editor with an integrated AI chatbot assistant. The chatbot allows users to request new features, which will be developed and integrated into the application in real-time.

## Features

✨ **Dark Mode UI** - Beautiful, modern dark theme interface  
📝 **Code Editor** - Full-featured text editor (2/3 of screen width)  
🤖 **AI Assistant Chatbot** - Interactive chatbot interface (1/3 of screen width)  
💾 **Save Functionality** - Save your code snippets  
▶️ **Run Button** - Execute your code (placeholder for future implementation)  
🎨 **Responsive Design** - Works on desktop and tablet devices  

## Screenshots

### Main Interface
![Self-Building App Interface](https://github.com/user-attachments/assets/2c2fbf06-489f-4b93-afac-e077ad626638)

### Chat Interaction
![Chat Demo](https://github.com/user-attachments/assets/9d9d9b91-f38f-4cb3-a6f0-0e6ca8621d7b)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

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

3. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**
   ```bash
   python manage.py runserver
   ```

5. **Open your browser**
   Navigate to `http://localhost:8000`

## Usage

### Code Editor
- Type or paste your code in the left panel (occupies 2/3 of the screen)
- Edit the filename in the input field at the top
- Use the **Save** button to save your code
- Use the **Run** button to execute code (coming soon)
- Tab key inserts 4 spaces for proper code indentation

### AI Assistant
- The chatbot appears on the right side (occupies 1/3 of the screen)
- Type your feature request in the text area at the bottom
- Press **Send** or hit Enter to submit your request
- The AI will respond with acknowledgment (full AI integration coming soon)

### Feature Requests
Users can request features like:
- "Add user authentication"
- "Create a database for saving projects"
- "Add syntax highlighting"
- "Implement code execution"

The chatbot will acknowledge requests and, in future versions, will automatically develop and integrate the requested features.

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

- **Backend**: Django 6.0+
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite (default, can be configured for PostgreSQL/MySQL)
- **Styling**: Custom CSS with dark mode theme

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
- `POST /api/save/` - Save code snippet

## Future Roadmap

🔄 **Phase 1** (Current) - Basic UI and chat interface  
🔄 **Phase 2** - AI agent integration for processing feature requests  
⏳ **Phase 3** - Automatic code generation and feature implementation  
⏳ **Phase 4** - Code execution environment  
⏳ **Phase 5** - User authentication and project management  
⏳ **Phase 6** - Real-time collaboration features  

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: This is an early-stage project. The AI-powered feature development capability is under active development. Currently, the chatbot provides acknowledgment responses, but full autonomous feature development will be implemented in future versions.
