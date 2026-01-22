// Initialize code editor
const editor = document.getElementById('editor');
const filenameInput = document.getElementById('filename');

// Get CSRF token from Django template
function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        return csrfInput.value;
    }
    // Fallback to cookie method
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Handle tab key in editor
editor.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        
        // Insert tab
        this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
        
        // Put cursor at right position
        this.selectionStart = this.selectionEnd = start + 4;
    }
});

// Chat functionality
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const strong = document.createElement('strong');
    strong.textContent = isUser ? 'You:' : 'AI Assistant:';
    
    const p = document.createElement('p');
    p.textContent = content;
    
    messageContent.appendChild(strong);
    messageContent.appendChild(p);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message typing-indicator';
    messageDiv.id = 'typing-indicator';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const strong = document.createElement('strong');
    strong.textContent = 'AI Assistant:';
    
    const p = document.createElement('p');
    p.innerHTML = '<span class="loading"></span> Thinking...';
    
    messageContent.appendChild(strong);
    messageContent.appendChild(p);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, true);
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable send button
    sendBtn.disabled = true;
    
    try {
        // Send message to backend
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.status === 'success') {
            addMessage(data.response, false);
        } else {
            addMessage('Sorry, there was an error processing your request.', false);
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('Sorry, there was an error connecting to the server.', false);
        console.error('Error:', error);
    } finally {
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// Event listeners for chat
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Save button functionality
document.getElementById('saveBtn').addEventListener('click', async function() {
    const code = editor.value;
    const filename = filenameInput.value;
    
    try {
        const response = await fetch('/api/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ code: code, filename: filename })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Show success message in chat
            addMessage(`✅ ${data.message}`, false);
        }
    } catch (error) {
        addMessage('❌ Error saving file.', false);
        console.error('Error:', error);
    }
});

// Run button functionality (placeholder)
document.getElementById('runBtn').addEventListener('click', function() {
    const code = editor.value;
    addMessage('Code execution is coming soon! For now, your code is ready in the editor.', false);
});

