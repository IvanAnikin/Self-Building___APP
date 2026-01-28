from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
import json
from .models import ChatMessage, CodeSnippet, FeatureRequest, CodeExecution, UserProfile, FeatureVersion, TestResult
from .ai_service import ai_service
from .code_executor import code_executor
from .feature_implementer import feature_implementer


# Phase 5: Authentication Views

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Initialize user profile if it doesn't exist
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(
                    user=user,
                    git_branch_name=f"user-{user.id}-workspace"
                )
            
            # Initialize git branch for user
            from .git_service import GitService
            git_service = GitService(user)
            git_service.initialize_user_branch()
            
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'editor/login.html')


def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validate inputs
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return render(request, 'editor/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'editor/register.html')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'editor/register.html')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            git_branch_name=f"user-{user.id}-workspace"
        )
        
        # Initialize git branch
        from .git_service import GitService
        git_service = GitService(user)
        git_service.initialize_user_branch()
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Account created successfully!')
        
        return redirect('index')
    
    return render(request, 'editor/register.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')


# Main application view
@login_required
def index(request):
    """Main view for the editor and chatbot interface"""
    return render(request, 'editor/index.html', {
        'user': request.user
    })

@login_required
def chat(request):
    """Handle chat messages from the user with AI integration"""
    print("\n" + "="*80)
    print(f"🔵 CHAT REQUEST RECEIVED from user: {request.user.username}")
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
            
            # Get recent conversation history for context (USER-SPECIFIC)
            print(f"🔍 Fetching conversation history for user {request.user.username}...")
            recent_messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:10]
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
            
            # Save user message to database (WITH USER)
            print(f"💾 Saving user message to database...")
            user_chat = ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response='',
                is_user=True
            )
            print(f"✅ User message saved (ID: {user_chat.id})")
            
            # Save AI response to database (WITH USER)
            print(f"💾 Saving AI response to database...")
            bot_chat = ChatMessage.objects.create(
                user=request.user,
                message=response_message,
                response='',
                is_user=False
            )
            print(f"✅ AI response saved (ID: {bot_chat.id})")
            
            # Check if this is a feature request and save it (WITH USER)
            is_feature_req = _is_feature_request(user_message)
            print(f"🔍 Feature Request Detected: {is_feature_req}")
            if is_feature_req:
                feature = FeatureRequest.objects.create(
                    user=request.user,
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

@login_required
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
            
            # Save to database (WITH USER)
            snippet = CodeSnippet.objects.create(
                user=request.user,
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

@login_required
def execute_code(request):
    """Handle code execution from the editor"""
    print("\n" + "="*80)
    print(f"🔵 CODE EXECUTION REQUEST from user: {request.user.username}")
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
            
            # Save execution record to database (WITH USER)
            print(f"💾 Saving execution record to database...")
            execution = CodeExecution.objects.create(
                user=request.user,
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


@login_required
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
            print(f"📊 Full Analysis Result:")
            print(json.dumps(analysis, indent=2))
            
            if analysis.get('feasible'):
                # Store the entire analysis as JSON, not just the plan string
                feature.implementation_plan = json.dumps(analysis)
                feature.status = 'approved'
                print(f"💾 Stored implementation plan ({len(feature.implementation_plan)} chars)")
            else:
                feature.error_log = analysis.get('reason', 'Analysis failed')
                feature.status = 'failed'
                print(f"❌ Feature marked as failed: {feature.error_log}")
            
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


@login_required
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
                print(f"❌ No implementation plan found")
                return JsonResponse({
                    'status': 'error',
                    'error': 'Feature must be analyzed first'
                }, status=400)
            
            print(f"📋 Implementation Plan (first 200 chars):")
            print(feature.implementation_plan[:200])
            
            # For now, generate code preview without applying
            # This is Phase 4 Part 1 - code generation and preview
            # Part 2 will handle actual application of changes
            
            # Parse implementation plan
            try:
                plan_data = json.loads(feature.implementation_plan)
                print(f"✅ Successfully parsed implementation plan")
                print(f"📁 Files to modify: {plan_data.get('files_to_modify', [])}")
                files_to_modify = plan_data.get('files_to_modify', [])
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ JSON parsing error: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'error': 'Invalid implementation plan format'
                }, status=400)
            
            generated_files = []
            
            
            max_files_to_process = 5
            for file_path in files_to_modify[:max_files_to_process]:
                print(f"📝 Generating code for {file_path}...")
                
                # Read existing file content using feature_implementer's safe method
                file_info = feature_implementer.read_file_safely(file_path)
                existing_code = None
                
                if file_info['exists']:
                    if file_info['content']:
                        existing_code = file_info['content']
                        print(f"✅ File exists, read {len(existing_code)} characters")
                    else:
                        print(f"⚠️  File exists but couldn't read: {file_info['error']}")
                else:
                    print(f"ℹ️  File does not exist, will generate new file")
                
                # Generate code with existing context
                result = feature_implementer.generate_code(
                    feature.description,
                    feature.implementation_plan,
                    file_path,
                    existing_code=existing_code
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


@login_required
def list_features(request):
    """List all feature requests for the current user"""
    try:
        features = FeatureRequest.objects.filter(user=request.user)[:20]  # Last 20 features
        
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


@login_required
def preview_feature_changes(request):
    """Preview changes that would be made by a feature implementation"""
    print("\n" + "="*80)
    print("🔵 FEATURE PREVIEW REQUEST")
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
            
            print(f"📋 Previewing feature: {feature.description[:100]}...")
            
            if not feature.generated_code:
                return JsonResponse({
                    'status': 'error',
                    'error': 'No generated code found. Please implement the feature first.'
                }, status=400)
            
            # Parse generated code
            try:
                generated_files = json.loads(feature.generated_code)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Invalid generated code format'
                }, status=400)
            
            # Generate diffs for each file
            previews = []
            for file_info in generated_files:
                file_path = file_info.get('file')
                new_code = file_info.get('code', '')
                
                print(f"📄 Generating diff for {file_path}...")
                
                diff_info = feature_implementer.generate_diff(file_path, new_code)
                
                previews.append({
                    'file': file_path,
                    'diff': diff_info['diff'],
                    'additions': diff_info['additions'],
                    'deletions': diff_info['deletions'],
                    'file_exists': diff_info['file_exists'],
                    'changes': file_info.get('changes', []),
                    'notes': file_info.get('notes', '')
                })
            
            print(f"✅ Generated previews for {len(previews)} file(s)")
            
            return JsonResponse({
                'status': 'success',
                'previews': previews,
                'feature_id': feature.id,
                'description': feature.description
            })
            
        except Exception as e:
            print(f"❌ ERROR in preview_feature_changes: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'error': f'Error generating preview: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


@login_required
def apply_feature_changes(request):
    """Apply approved feature changes to actual files"""
    print("\n" + "="*80)
    print("🔵 APPLY FEATURE CHANGES REQUEST")
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
            
            print(f"🛠️ Applying changes for feature: {feature.description[:100]}...")
            
            if not feature.generated_code:
                return JsonResponse({
                    'status': 'error',
                    'error': 'No generated code found'
                }, status=400)
            
            # Parse generated code
            try:
                generated_files = json.loads(feature.generated_code)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Invalid generated code format'
                }, status=400)
            
            # Apply changes to each file
            applied_files = []
            errors = []
            
            for file_info in generated_files:
                file_path = file_info.get('file')
                new_code = file_info.get('code', '')
                
                print(f"📝 Applying changes to {file_path}...")
                
                result = feature_implementer.apply_changes(
                    file_path=file_path,
                    content=new_code,
                    backup=True
                )
                
                if result.get('success'):
                    applied_files.append({
                        'file': file_path,
                        'backup_created': result.get('backup_created', False)
                    })
                    print(f"✅ Successfully applied changes to {file_path}")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    errors.append({
                        'file': file_path,
                        'error': error_msg
                    })
                    print(f"❌ Failed to apply changes to {file_path}: {error_msg}")
            
            # Update feature status
            if errors:
                feature.status = 'failed'
                feature.error_log = json.dumps(errors)
                print(f"⚠️ Feature partially failed with {len(errors)} error(s)")
            else:
                feature.status = 'completed'
                feature.completed_at = timezone.now()
                print(f"✅ Feature completed successfully")
                
                # Phase 5: Git commit integration
                try:
                    from .git_service import GitService
                    
                    git_service = GitService(request.user)
                    
                    # Get list of modified files
                    modified_files = [f['file'] for f in applied_files]
                    feature.files_modified = modified_files
                    
                    # Commit changes to user's branch
                    commit_message = f"feat: {feature.description[:100]}"
                    commit_hash = git_service.commit_changes(
                        message=commit_message,
                        files=modified_files
                    )
                    
                    if commit_hash:
                        feature.git_commit_hash = commit_hash
                        print(f"✅ Git commit created: {commit_hash[:7]}")
                        
                        # Create FeatureVersion record
                        code_snapshot = {f['file']: file_info.get('code', '') 
                                       for f, file_info in zip(applied_files, generated_files)}
                        
                        FeatureVersion.objects.create(
                            user=request.user,
                            feature=feature,
                            commit_hash=commit_hash,
                            commit_message=commit_message,
                            files_changed=modified_files,
                            code_snapshot=code_snapshot,
                            status='active'
                        )
                        print(f"✅ FeatureVersion record created")
                    else:
                        print(f"⚠️ Git commit failed, but feature applied successfully")
                        
                except Exception as git_error:
                    print(f"⚠️ Git commit error (feature still applied): {git_error}")
                    # Don't fail the entire operation if git fails
            
            feature.save()
            
            response_data = {
                'status': 'success' if not errors else 'partial',
                'message': f'Applied changes to {len(applied_files)} file(s)',
                'applied_files': applied_files,
                'errors': errors,
                'feature_id': feature.id
            }
            
            # Add commit hash to response if available
            if hasattr(feature, 'git_commit_hash') and feature.git_commit_hash:
                response_data['commit_hash'] = feature.git_commit_hash
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ ERROR in apply_feature_changes: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if 'feature' in locals():
                feature.status = 'failed'
                feature.error_log = str(e)
                feature.save()
            
            return JsonResponse({
                'status': 'error',
                'error': f'Error applying changes: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


@login_required
def reject_feature_changes(request):
    """Reject feature changes and mark as rejected"""
    print("\n" + "="*80)
    print("🔵 REJECT FEATURE CHANGES REQUEST")
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
            
            print(f"🚫 Rejecting feature: {feature.description[:100]}...")
            
            # Update status to rejected
            feature.status = 'rejected'
            feature.save()
            
            print(f"✅ Feature marked as rejected")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Feature changes rejected',
                'feature_id': feature.id
            })
            
        except Exception as e:
            print(f"❌ ERROR in reject_feature_changes: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'status': 'error',
                'error': f'Error rejecting feature: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'error': 'Only POST requests are allowed'}, status=405)


# Phase 5: Version Control Endpoints

@login_required
def get_version_history(request):
    """Get version history for the current user"""
    try:
        from .git_service import GitService
        
        git_service = GitService(request.user)
        commits = git_service.get_commit_history(limit=50)
        
        return JsonResponse({
            'status': 'success',
            'versions': commits,
            'current_branch': git_service.branch_name
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': f'Error getting version history: {str(e)}'
        }, status=500)


@login_required
def switch_version(request):
    """Switch to a specific version (commit)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commit_hash = data.get('commit_hash')
            
            if not commit_hash:
                return JsonResponse({
                    'status': 'error',
                    'error': 'commit_hash is required'
                }, status=400)
            
            from .git_service import GitService
            
            git_service = GitService(request.user)
            success = git_service.checkout_commit(commit_hash)
            
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Switched to version {commit_hash[:7]}',
                    'commit_hash': commit_hash
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'error': 'Failed to switch version'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': f'Error switching version: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'error': 'Only POST requests are allowed'
    }, status=405)
