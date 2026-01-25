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

function addMessage(content, isUser = false, featureRequestId = null) {
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
    
    // Add "Implement Feature" button if this is a feature request
    if (featureRequestId && !isUser) {
        const implementBtn = document.createElement('button');
        implementBtn.className = 'btn btn-primary btn-sm implement-feature-btn';
        implementBtn.textContent = '🚀 Implement This Feature';
        implementBtn.style.marginTop = '10px';
        implementBtn.onclick = () => implementFeature(featureRequestId);
        messageContent.appendChild(implementBtn);
    }
    
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
        // Get current code from editor for context (optional)
        const codeContext = editor.value.trim();
        
        // Send message to backend
        const response = await fetch(window.API_URLS.chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ 
                message: message,
                code_context: codeContext || null
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.status === 'success') {
            // Add message with feature request button if applicable
            const featureId = data.is_feature_request ? data.feature_request_id : null;
            addMessage(data.response, false, featureId);
            
            // Show AI status badge if available
            if (data.ai_enabled) {
                console.log('AI service is enabled and processing requests');
            }
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
        const response = await fetch(window.API_URLS.save, {
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

// Output section management
const outputSection = document.getElementById('outputSection');
const outputContent = document.getElementById('outputContent');
const clearOutputBtn = document.getElementById('clearOutputBtn');
const editorSection = document.querySelector('.editor-section');

function showOutput(content, isError = false) {
    outputSection.style.display = 'flex';
    outputContent.textContent = content;
    outputContent.className = 'output-content ' + (isError ? 'error' : 'success');
    editorSection.classList.add('with-output');
}

function hideOutput() {
    outputSection.style.display = 'none';
    outputContent.textContent = '';
    editorSection.classList.remove('with-output');
}

clearOutputBtn.addEventListener('click', function() {
    hideOutput();
});

// Detect language from filename
function detectLanguage(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const langMap = {
        'py': 'python',
        'js': 'javascript',
        'mjs': 'javascript',
        'cjs': 'javascript',
        'node': 'javascript'
    };
    return langMap[ext] || 'python';
}

// Run button functionality with code execution
document.getElementById('runBtn').addEventListener('click', async function() {
    const code = editor.value.trim();
    const filename = filenameInput.value || 'main.py';
    const language = detectLanguage(filename);
    
    if (!code) {
        showOutput('Error: No code to execute', true);
        return;
    }
    
    // Show execution indicator
    showOutput(`🔄 Executing ${language} code...\n`, false);
    addMessage(`⚙️ Running ${filename}...`, false);
    
    try {
        const response = await fetch('/api/execute/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                code: code,
                language: language,
                filename: filename
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Display stdout
            let output = '';
            if (data.stdout) {
                output += data.stdout;
            }
            if (!output) {
                output = '✅ Program executed successfully (no output)';
            }
            showOutput(output, false);
            addMessage(`✅ Code executed successfully!`, false);
        } else {
            // Display error
            let errorOutput = '';
            if (data.error) {
                errorOutput += `❌ Error: ${data.error}\n\n`;
            }
            if (data.stderr) {
                errorOutput += data.stderr;
            }
            if (data.stdout) {
                errorOutput += '\n--- Output before error ---\n' + data.stdout;
            }
            showOutput(errorOutput || '❌ Unknown error occurred', true);
            addMessage(`❌ Execution failed. Check the output panel for details.`, false);
        }
    } catch (error) {
        showOutput(`❌ Error: ${error.message}`, true);
        addMessage('❌ Error executing code.', false);
        console.error('Error:', error);
    }
});


// Phase 4: Feature Implementation
async function implementFeature(featureId) {
    addMessage(`🔍 Analyzing feature request #${featureId}...`, false);
    
    try {
        // Step 1: Analyze the feature
        const analyzeResponse = await fetch('/api/features/analyze/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ feature_id: featureId })
        });
        
        const analyzeData = await analyzeResponse.json();
        
        if (analyzeData.status !== 'success') {
            addMessage(`❌ Analysis failed: ${analyzeData.error}`, false);
            return;
        }
        
        const analysis = analyzeData.analysis;
        
        if (!analysis.feasible) {
            addMessage(`❌ Feature not feasible: ${analysis.reason}`, false);
            return;
        }
        
        addMessage(`✅ Feature is feasible! Complexity: ${analysis.estimated_complexity}`, false);
        
        // Safely display plan
        const plan = analysis.plan || '';
        const planPreview = plan.length > 200 ? plan.substring(0, 200) + '...' : plan;
        if (planPreview) {
            addMessage(`📋 Plan: ${planPreview}`, false);
        }
        
        // Step 2: Generate code
        addMessage(`🛠️ Generating code...`, false);
        
        const implementResponse = await fetch('/api/features/implement/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ feature_id: featureId })
        });
        
        const implementData = await implementResponse.json();
        
        if (implementData.status !== 'success') {
            addMessage(`❌ Code generation failed: ${implementData.error}`, false);
            return;
        }
        
        const generated = implementData.generated_files;
        
        addMessage(`✅ Code generated for ${generated.length} file(s)!`, false);
        
        for (const file of generated) {
            addMessage(`📄 ${file.file}: ${file.changes.join(', ')}`, false);
        }
        
        addMessage(`🎉 Feature implementation preview ready! (Actual application of changes will be added in Phase 4 Part 2)`, false);
        
    } catch (error) {
        addMessage(`❌ Error: ${error.message}`, false);
        console.error('Feature implementation error:', error);
    }
}
