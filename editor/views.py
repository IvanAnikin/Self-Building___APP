from django.shortcuts import render
from django.http import JsonResponse
import json

def index(request):
    """Main view for the editor and chatbot interface"""
    return render(request, 'editor/index.html')

def chat(request):
    """Handle chat messages from the user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Simple response for now - in the future, this will integrate with an AI agent
            response_message = f"I received your request: '{user_message}'. In the future, I will be able to help you modify the app based on your requirements. This feature is under development."
            
            return JsonResponse({
                'status': 'success',
                'response': response_message
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

def save_code(request):
    """Handle saving code from the editor"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            filename = data.get('filename', 'untitled.txt')
            
            # For now, just acknowledge the save
            # In the future, this could actually save files to a user workspace
            return JsonResponse({
                'status': 'success',
                'message': f'Code saved as {filename}'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

