// Initialize code editor
const editor = document.getElementById('editor');
const filenameInput = document.getElementById('filename');
const lineNumbers = document.getElementById('lineNumbers');

// Line numbers functionality
function updateLineNumbers() {
    const lines = editor.value.split('\n');
    const lineCount = lines.length;
    
    let lineNumbersHtml = '';
    for (let i = 1; i <= lineCount; i++) {
        lineNumbersHtml += `<div>${i}</div>`;
    }
    
    lineNumbers.innerHTML = lineNumbersHtml;
}

// Update line numbers on input
editor.addEventListener('input', updateLineNumbers);
editor.addEventListener('scroll', function() {
    // Sync scroll between line numbers and editor
    lineNumbers.scrollTop = editor.scrollTop;
});

// Initialize line numbers on page load
updateLineNumbers();

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
        
        // Step 3: Show review changes button
        addMessage(`📋 Changes are ready for review. Click the button below to review and approve or reject.`, false);
        
        // Add review button
        const reviewMessage = document.createElement('div');
        reviewMessage.className = 'message bot-message';
        reviewMessage.innerHTML = `
            <div class="message-content">
                <button class="btn btn-primary review-changes-btn" data-feature-id="${featureId}">
                    👁️ Review Changes
                </button>
            </div>
        `;
        chatMessages.appendChild(reviewMessage);
        
        // Add event listener for the review button
        reviewMessage.querySelector('.review-changes-btn').addEventListener('click', function() {
            reviewFeatureChanges(this.getAttribute('data-feature-id'));
        });
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
    } catch (error) {
        addMessage(`❌ Error: ${error.message}`, false);
        console.error('Feature implementation error:', error);
    }
}

// Phase 4 Part 3: Review feature changes
async function reviewFeatureChanges(featureId) {
    addMessage(`📋 Loading change preview for feature #${featureId}...`, false);
    
    try {
        const response = await fetch('/api/features/preview/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ feature_id: featureId })
        });
        
        const data = await response.json();
        
        if (data.status !== 'success') {
            addMessage(`❌ Preview failed: ${data.error}`, false);
            return;
        }
        
        // Display preview information
        addMessage(`📊 Changes Preview for: "${data.description}"`, false);
        
        for (const preview of data.previews) {
            const status = preview.file_exists ? 'Modified' : 'New File';
            addMessage(`📄 ${preview.file} (${status}): +${preview.additions} lines, -${preview.deletions} lines`, false);
            
            if (preview.notes) {
                addMessage(`   ℹ️ ${preview.notes}`, false);
            }
        }
        
        // Show diff in a modal or expandable section
        showDiffModal(data, featureId);
        
    } catch (error) {
        addMessage(`❌ Error: ${error.message}`, false);
        console.error('Preview error:', error);
    }
}

// Show diff modal with approve/reject buttons
function showDiffModal(previewData, featureId) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'diffModal';
    
    let filesHtml = '';
    for (const preview of previewData.previews) {
        const status = preview.file_exists ? 'Modified' : 'New File';
        filesHtml += `
            <div class="file-preview">
                <h4>📄 ${preview.file} <span class="badge">${status}</span></h4>
                <div class="diff-stats">
                    <span class="additions">+${preview.additions}</span>
                    <span class="deletions">-${preview.deletions}</span>
                </div>
                <pre class="diff-content">${escapeHtml(preview.diff)}</pre>
                ${preview.notes ? `<p class="notes"><strong>Notes:</strong> ${escapeHtml(preview.notes)}</p>` : ''}
            </div>
        `;
    }
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Review Changes</h2>
                <button class="close-btn" data-action="close">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Feature:</strong> ${escapeHtml(previewData.description)}</p>
                ${filesHtml}
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger" data-action="reject" data-feature-id="${featureId}">
                    ❌ Reject Changes
                </button>
                <button class="btn btn-success" data-action="approve" data-feature-id="${featureId}">
                    ✅ Accept & Apply Changes
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners to buttons
    modal.querySelector('[data-action="close"]').addEventListener('click', closeDiffModal);
    modal.querySelector('[data-action="reject"]').addEventListener('click', function() {
        rejectFeatureChanges(this.getAttribute('data-feature-id'));
    });
    modal.querySelector('[data-action="approve"]').addEventListener('click', function() {
        approveFeatureChanges(this.getAttribute('data-feature-id'));
    });
}

function closeDiffModal() {
    const modal = document.getElementById('diffModal');
    if (modal) {
        modal.remove();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Approve and apply feature changes
async function approveFeatureChanges(featureId) {
    closeDiffModal();
    addMessage(`⏳ Applying approved changes for feature #${featureId}...`, false);
    
    try {
        const response = await fetch('/api/features/apply/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ feature_id: featureId })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addMessage(`✅ ${data.message}`, false);
            
            for (const file of data.applied_files) {
                const backup = file.backup_created ? ' (backup created)' : '';
                addMessage(`   ✓ ${file.file}${backup}`, false);
            }
            
            addMessage(`🎉 Feature implementation complete! The changes have been applied to your application.`, false);
            
        } else if (data.status === 'partial') {
            addMessage(`⚠️ ${data.message}`, false);
            
            for (const file of data.applied_files) {
                addMessage(`   ✓ ${file.file}`, false);
            }
            
            for (const error of data.errors) {
                addMessage(`   ❌ ${error.file}: ${error.error}`, false);
            }
            
        } else {
            addMessage(`❌ Failed to apply changes: ${data.error}`, false);
        }
        
    } catch (error) {
        addMessage(`❌ Error applying changes: ${error.message}`, false);
        console.error('Apply changes error:', error);
    }
}

// Reject feature changes
async function rejectFeatureChanges(featureId) {
    closeDiffModal();
    addMessage(`🚫 Rejecting changes for feature #${featureId}...`, false);
    
    try {
        const response = await fetch('/api/features/reject/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ feature_id: featureId })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addMessage(`✅ ${data.message}. The generated code has been discarded.`, false);
        } else {
            addMessage(`❌ Failed to reject changes: ${data.error}`, false);
        }
        
    } catch (error) {
        addMessage(`❌ Error rejecting changes: ${error.message}`, false);
        console.error('Reject changes error:', error);
    }
}

// ============================================================================
// Phase 5: Version Control Functions
// ============================================================================

let currentVersionHash = null;

// Load and display version history
async function loadVersionHistory() {
    const timeline = document.getElementById('versionTimeline');
    
    // Show loading state
    timeline.innerHTML = '<div class="loading-versions"><span>Loading versions...</span></div>';
    
    try {
        const response = await fetch('/api/versions/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            displayVersionHistory(data.versions, data.current_branch);
            
            // Store current version (latest commit)
            if (data.versions && data.versions.length > 0) {
                currentVersionHash = data.versions[0].hash;
            }
        } else {
            timeline.innerHTML = `<div class="version-error">⚠️ ${data.error || 'Failed to load versions'}</div>`;
        }
        
    } catch (error) {
        console.error('Error loading versions:', error);
        timeline.innerHTML = '<div class="version-error">❌ Error loading version history</div>';
    }
}

// Display version history in the UI
function displayVersionHistory(versions, currentBranch) {
    const timeline = document.getElementById('versionTimeline');
    
    if (!versions || versions.length === 0) {
        timeline.innerHTML = `
            <div class="empty-versions">
                <div class="icon">📋</div>
                <p>No version history yet.</p>
                <p style="font-size: 0.85rem;">Versions will appear here after you apply features.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    versions.forEach((version, index) => {
        const isCurrentVersion = index === 0;
        const versionClass = isCurrentVersion ? 'version-item current' : 'version-item';
        const shortHash = version.hash.substring(0, 7);
        
        html += `
            <div class="${versionClass}" onclick="switchToVersion('${version.hash}', '${shortHash}')">
                <div class="version-hash">${shortHash}</div>
                <div class="version-message">${escapeHtml(version.message)}</div>
                <div class="version-meta">
                    <span class="version-date">📅 ${version.date}</span>
                    <span class="version-author">👤 ${escapeHtml(version.author)}</span>
                </div>
            </div>
        `;
    });
    
    timeline.innerHTML = html;
}

// Switch to a specific version
async function switchToVersion(commitHash, shortHash) {
    if (!confirm(`Switch to version ${shortHash}?\n\nThis will checkout this specific commit.`)) {
        return;
    }
    
    addMessage(`🔄 Switching to version ${shortHash}...`, false);
    
    try {
        const response = await fetch('/api/versions/switch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ commit_hash: commitHash })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addMessage(`✅ ${data.message}`, false);
            addMessage(`💡 Refresh the page to see the changes.`, false);
            
            // Reload version history
            loadVersionHistory();
        } else {
            addMessage(`❌ Failed to switch version: ${data.error}`, false);
        }
        
    } catch (error) {
        addMessage(`❌ Error switching version: ${error.message}`, false);
        console.error('Switch version error:', error);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Refresh version history button handler
document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refreshVersionsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadVersionHistory();
        });
    }
    
    // Load version history on page load
    loadVersionHistory();
});

// Update the approveFeatureChanges function to refresh versions after applying
const originalApproveFeatureChanges = window.approveFeatureChanges;
if (typeof originalApproveFeatureChanges === 'function') {
    window.approveFeatureChanges = async function(featureId) {
        await originalApproveFeatureChanges(featureId);
        
        // Reload version history after successful application
        setTimeout(() => {
            loadVersionHistory();
        }, 1000);
    };
}
