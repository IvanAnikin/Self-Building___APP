from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import ChatMessage, CodeSnippet, FeatureRequest, CodeExecution
from .ai_service import ai_service
from .code_executor import code_executor
from .feature_implementer import feature_implementer

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
            else:
                feature = None
            
            print(f"✅ Request completed successfully")
            print("="*80 + "\n")
            
            response_data = {
                'status': 'success',
                'response': response_message,
                'ai_enabled': ai_service.is_enabled()
            }
            
            # Include feature request ID if one was created
            if feature:
                response_data['feature_request_id'] = feature.id
                response_data['is_feature_request'] = True
            
            return JsonResponse(response_data)
            
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
        'add a ', 'add an ', 'add some',
        'implement', 'create a', 'create an',
        'build a', 'build an',
        'can you add', 'could you add',
        'can you create', 'could you create',
        'can you implement', 'could you implement',
        'want to add', 'need to add',
        'would like to add', 'would like a',
        'i want', 'i need'
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

def execute_code(request):
    """Handle code execution from the editor"""
    print("\n" + "="*80)
    print("🔵 CODE EXECUTION REQUEST RECEIVED")
    print("="*80)
    
    if request.method == 'POST':
        try:
            # Parse request body
            data = json.loads(request.body)
            code = data.get('code', '')
            language = data.get('language', 'python')
            filename = data.get('filename', 'untitled.txt')
            
            print(f"📄 Filename: {filename}")
            print(f"🔤 Language: {language}")
            print(f"📝 Code Length: {len(code)} characters")
            
            if not code.strip():
                print("❌ Error: Empty code provided")
                return JsonResponse({
                    'status': 'error',
                    'error': 'Code cannot be empty',
                    'stdout': '',
                    'stderr': ''
                }, status=400)
            
            # Execute the code
            print(f"⚙️  Executing code...")
            result = code_executor.execute(code, language)
            
            print(f"✅ Execution Status: {result['status']}")
            print(f"📤 Return Code: {result.get('returncode', 'N/A')}")
            
            # Save execution record to database
            print(f"💾 Saving execution record to database...")
            execution = CodeExecution.objects.create(
                code=code,
                language=language,
                filename=filename,
                stdout=result.get('stdout', ''),
                stderr=result.get('stderr', ''),
                returncode=result.get('returncode', 0),
                status=result['status'],
                error_message=result.get('error') or ''
            )
            print(f"✅ Execution record saved (ID: {execution.id})")
            
            print(f"✅ Request completed successfully")
            print("="*80 + "\n")
            
            # Return execution result
            return JsonResponse({
                'status': result['status'],
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', ''),
                'returncode': result.get('returncode', 0),
                'error': result.get('error', None),
                'execution_id': execution.id
            })
            
        except Exception as e:
            print(f"❌ ERROR in execute_code view: {str(e)}")
            import traceback
            print(f"📍 Traceback:")
            traceback.print_exc()
            print("="*80 + "\n")
            return JsonResponse({
                'status': 'error',
                'error': f'Error executing code: {str(e)}',
                'stdout': '',
                'stderr': ''
            }, status=500)
    
    print("❌ Invalid request method (not POST)")
    print("="*80 + "\n")
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


def analyze_feature(request):
    """Analyze a feature request and create implementation plan"""
    print("\n" + "="*80)
    print("🔵 FEATURE ANALYSIS REQUEST")
    print("="*80)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feature_id = data.get('feature_id')
            
            if not feature_id:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature ID is required'
                }, status=400)
            
            # Get the feature request
            try:
                feature = FeatureRequest.objects.get(id=feature_id)
            except FeatureRequest.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature request not found'
                }, status=404)
            
            print(f"📋 Analyzing feature: {feature.description[:100]}...")
            
            # Update status
            feature.status = 'processing'
            feature.save()
            
            # Analyze the feature
            analysis = feature_implementer.analyze_feature_request(feature.description)
            
            print(f"✅ Analysis complete: Feasible={analysis.get('feasible', False)}")
            
            if analysis.get('feasible'):
                feature.implementation_plan = analysis.get('plan', '')
                feature.status = 'approved'
            else:
                feature.error_log = analysis.get('reason', 'Analysis failed')
                feature.status = 'failed'
            
            feature.save()
            
            return JsonResponse({
                'status': 'success',
                'analysis': analysis,
                'feature_id': feature.id
            })
            
        except Exception as e:
            print(f"❌ ERROR in analyze_feature: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'error': f'Error analyzing feature: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


def implement_feature(request):
    """Generate and apply code for a feature request"""
    print("\n" + "="*80)
    print("🔵 FEATURE IMPLEMENTATION REQUEST")
    print("="*80)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feature_id = data.get('feature_id')
            approve = data.get('approve', False)
            
            if not feature_id:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature ID is required'
                }, status=400)
            
            # Get the feature request
            try:
                feature = FeatureRequest.objects.get(id=feature_id)
            except FeatureRequest.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature request not found'
                }, status=404)
            
            print(f"🛠️  Implementing feature: {feature.description[:100]}...")
            
            if not feature.implementation_plan:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature must be analyzed first'
                }, status=400)
            
            # For now, generate code preview without applying
            # This is Phase 4 Part 1 - code generation and preview
            # Part 2 will handle actual application of changes
            
            files_to_modify = json.loads(feature.implementation_plan).get('files_to_modify', [])
            generated_files = []
            
            for file_path in files_to_modify[:1]:  # Start with first file for demo
                print(f"📝 Generating code for {file_path}...")
                
                result = feature_implementer.generate_code(
                    feature.description,
                    feature.implementation_plan,
                    file_path
                )
                
                if result.get('success'):
                    generated_files.append({
                        'file': file_path,
                        'code': result.get('code', ''),
                        'changes': result.get('changes_made', []),
                        'notes': result.get('notes', '')
                    })
            
            feature.generated_code = json.dumps(generated_files)
            feature.files_modified = [f['file'] for f in generated_files]
            feature.status = 'processing'
            feature.save()
            
            print(f"✅ Code generated for {len(generated_files)} file(s)")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Code generated successfully',
                'generated_files': generated_files,
                'feature_id': feature.id
            })
            
        except Exception as e:
            print(f"❌ ERROR in implement_feature: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if 'feature' in locals():
                feature.status = 'failed'
                feature.error_log = str(e)
                feature.save()
            
            return JsonResponse({
                'status': 'error',
                'error': f'Error implementing feature: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


def list_features(request):
    """List all feature requests with their status"""
    try:
        features = FeatureRequest.objects.all()[:20]  # Last 20 features
        
        features_data = [{
            'id': f.id,
            'description': f.description,
            'status': f.status,
            'created_at': f.created_at.isoformat(),
            'completed_at': f.completed_at.isoformat() if f.completed_at else None,
            'has_plan': bool(f.implementation_plan),
            'has_code': bool(f.generated_code),
        } for f in features]
        
        return JsonResponse({
            'status': 'success',
            'features': features_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': f'Error listing features: {str(e)}'
        }, status=500)
