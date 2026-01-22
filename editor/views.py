from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import ChatMessage, CodeSnippet, FeatureRequest
from .ai_service import ai_service

def index(request):
    """Main view for the editor and chatbot interface"""
    return render(request, 'editor/index.html')

def chat(request):
    """Handle chat messages from the user with AI integration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            code_context = data.get('code_context', None)  # Optional: current code from editor
            
            if not user_message:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Message cannot be empty'
                }, status=400)
            
            # Get recent conversation history for context
            recent_messages = ChatMessage.objects.all()[:10]
            conversation_history = [
                {
                    'message': msg.message,
                    'is_user': msg.is_user
                }
                for msg in reversed(list(recent_messages))
            ]
            
            # Process message with AI service
            ai_response_data = ai_service.process_message(
                user_message=user_message,
                conversation_history=conversation_history,
                code_context=code_context
            )
            
            response_message = ai_response_data.get('response', '')
            
            # Save user message to database
            user_chat = ChatMessage.objects.create(
                message=user_message,
                response='',
                is_user=True
            )
            
            # Save AI response to database
            bot_chat = ChatMessage.objects.create(
                message=response_message,
                response='',
                is_user=False
            )
            
            # Check if this is a feature request and save it
            if _is_feature_request(user_message):
                FeatureRequest.objects.create(
                    description=user_message,
                    status='pending'
                )
            
            return JsonResponse({
                'status': 'success',
                'response': response_message,
                'ai_enabled': ai_service.is_enabled()
            })
            
        except Exception as e:
            print(f"Chat error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

def _is_feature_request(message):
    """Simple heuristic to detect if a message is a feature request"""
    keywords = ['add', 'implement', 'create', 'feature', 'build', 'make', 'want', 'need', 'can you']
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in keywords)

def save_code(request):
    """Handle saving code from the editor to database"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            filename = data.get('filename', 'untitled.txt')
            
            # Detect language from filename extension
            language = 'text'
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
                language_map = {
                    'py': 'python',
                    'js': 'javascript',
                    'html': 'html',
                    'css': 'css',
                    'java': 'java',
                    'cpp': 'cpp',
                    'c': 'c',
                    'go': 'go',
                    'rs': 'rust',
                    'rb': 'ruby',
                    'php': 'php',
                }
                language = language_map.get(ext, ext)
            
            # Save to database
            snippet = CodeSnippet.objects.create(
                filename=filename,
                code=code,
                language=language
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Code saved as {filename}',
                'snippet_id': snippet.id
            })
            
        except Exception as e:
            print(f"Save error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving code: {str(e)}'
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

