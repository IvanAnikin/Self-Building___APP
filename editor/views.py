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
    print("\n" + "="*80)
    print("🔵 CHAT REQUEST RECEIVED")
    print("="*80)
    
    if request.method == 'POST':
        try:
            # Parse request body
            data = json.loads(request.body)
            user_message = data.get('message', '')
            code_context = data.get('code_context', None)
            
            print(f"📨 User Message: '{user_message}'")
            print(f"📝 Code Context Included: {code_context is not None}")
            
            if not user_message:
                print("❌ Error: Empty message received")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Message cannot be empty'
                }, status=400)
            
            # Get recent conversation history for context
            print(f"🔍 Fetching conversation history...")
            recent_messages = ChatMessage.objects.order_by('-timestamp')[:10]
            conversation_history = [
                {
                    'message': msg.message,
                    'is_user': msg.is_user
                }
                for msg in reversed(list(recent_messages))
            ]
            print(f"📚 Found {len(conversation_history)} previous messages in history")
            
            # Check AI service status
            print(f"🤖 AI Service Enabled: {ai_service.is_enabled()}")
            if ai_service.is_enabled():
                print(f"🔧 Using OpenAI Model: {ai_service.model}")
            else:
                print("⚠️  AI Service Disabled - Using Fallback Responses")
            
            # Process message with AI service
            print(f"⚙️  Processing message with AI service...")
            ai_response_data = ai_service.process_message(
                user_message=user_message,
                conversation_history=conversation_history,
                code_context=code_context
            )
            
            response_message = ai_response_data.get('response', '')
            ai_status = ai_response_data.get('status', 'unknown')
            print(f"✅ AI Response Status: {ai_status}")
            print(f"💬 AI Response (first 100 chars): {response_message[:100]}...")
            
            # Save user message to database
            print(f"💾 Saving user message to database...")
            user_chat = ChatMessage.objects.create(
                message=user_message,
                response='',
                is_user=True
            )
            print(f"✅ User message saved (ID: {user_chat.id})")
            
            # Save AI response to database
            print(f"💾 Saving AI response to database...")
            bot_chat = ChatMessage.objects.create(
                message=response_message,
                response='',
                is_user=False
            )
            print(f"✅ AI response saved (ID: {bot_chat.id})")
            
            # Check if this is a feature request and save it
            is_feature_req = _is_feature_request(user_message)
            print(f"🔍 Feature Request Detected: {is_feature_req}")
            if is_feature_req:
                feature = FeatureRequest.objects.create(
                    description=user_message,
                    status='pending'
                )
                print(f"📋 Feature request created (ID: {feature.id})")
            
            print(f"✅ Request completed successfully")
            print("="*80 + "\n")
            
            return JsonResponse({
                'status': 'success',
                'response': response_message,
                'ai_enabled': ai_service.is_enabled()
            })
            
        except Exception as e:
            print(f"❌ ERROR in chat view: {str(e)}")
            import traceback
            print(f"📍 Traceback:")
            traceback.print_exc()
            print("="*80 + "\n")
            return JsonResponse({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=400)
    
    print("❌ Invalid request method (not POST)")
    print("="*80 + "\n")
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

def _is_feature_request(message):
    """Simple heuristic to detect if a message is a feature request"""
    # More specific patterns for feature requests
    feature_patterns = [
        'add feature', 'add a feature', 'add the feature',
        'implement', 'create a', 'create an',
        'build a', 'build an',
        'can you add', 'could you add',
        'can you create', 'could you create',
        'can you implement', 'could you implement',
        'want to add', 'need to add',
        'would like to add', 'would like a'
    ]
    message_lower = message.lower()
    return any(pattern in message_lower for pattern in feature_patterns)

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

