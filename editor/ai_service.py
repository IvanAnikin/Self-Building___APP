"""
AI Service for processing user requests and providing intelligent responses.
This module integrates with OpenAI API to power the AI assistant chatbot.
"""
import os
from openai import OpenAI
from django.conf import settings


class AIService:
    """Service class for handling AI-powered chat interactions"""
    
    def __init__(self):
        """Initialize the AI service with OpenAI client"""
        api_key = os.environ.get('OPENAI_API_KEY', '')
        if not api_key:
            self.client = None
            self.enabled = False
        else:
            self.client = OpenAI(api_key=api_key)
            self.enabled = True
            self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    
    def is_enabled(self):
        """Check if AI service is properly configured"""
        return self.enabled
    
    def get_system_prompt(self):
        """Get the system prompt that defines the AI assistant's behavior"""
        return """You are an intelligent AI assistant for the Self-Building App, a code editor 
with AI-powered feature development capabilities. Your role is to:

1. Help users with coding questions and problems
2. Understand feature requests and provide guidance on implementation
3. Suggest code improvements and best practices
4. Be friendly, helpful, and concise in your responses
5. When users request new features, acknowledge the request and explain what would be needed

Keep responses conversational and helpful. You are working within a web-based code editor 
environment where users can write and save code."""
    
    def process_message(self, user_message, conversation_history=None, code_context=None):
        """
        Process a user message and generate an AI response
        
        Args:
            user_message: The message from the user
            conversation_history: Optional list of previous messages for context
            code_context: Optional current code from the editor for context
            
        Returns:
            dict: Response with status and message
        """
        print(f"  🧠 AI Service: process_message called")
        print(f"     - Message length: {len(user_message)} chars")
        print(f"     - History items: {len(conversation_history) if conversation_history else 0}")
        print(f"     - Code context: {'Yes' if code_context else 'No'}")
        
        if not self.enabled:
            print(f"  ⚠️  AI Service: Not enabled, using fallback")
            return {
                'status': 'fallback',
                'response': self._get_fallback_response(user_message)
            }
        
        try:
            print(f"  🔧 AI Service: Building API request...")
            # Build messages for the API
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                history_count = len(conversation_history[-10:])
                print(f"     - Adding {history_count} history messages")
                for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                    messages.append({
                        "role": "user" if msg.get('is_user') else "assistant",
                        "content": msg.get('message', '')
                    })
            
            # Add the current user message
            current_message = user_message
            
            # Add code context if provided
            if code_context:
                print(f"     - Adding code context ({len(code_context)} chars)")
                current_message += f"\n\n[Current code in editor]:\n```\n{code_context}\n```"
            
            messages.append({"role": "user", "content": current_message})
            print(f"     - Total messages to API: {len(messages)}")
            
            # Call OpenAI API
            print(f"  🌐 AI Service: Calling OpenAI API (model: {self.model})...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            print(f"  ✅ AI Service: Received response ({len(ai_response)} chars)")
            print(f"     - Tokens used: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")
            
            return {
                'status': 'success',
                'response': ai_response
            }
            
        except Exception as e:
            print(f"  ❌ AI Service Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'response': self._get_fallback_response(user_message),
                'error': str(e)
            }
    
    def _get_fallback_response(self, user_message):
        """Generate a fallback response when AI is not available"""
        message_lower = user_message.lower()
        
        # Simple keyword-based responses
        if any(word in message_lower for word in ['feature', 'add', 'implement', 'create']):
            return ("Thank you for your feature request! I've noted it down. "
                   "Full AI-powered feature development is being enhanced. "
                   "For now, I can acknowledge your request and it will be tracked in the system.")
        
        elif any(word in message_lower for word in ['help', 'how', 'what', 'explain']):
            return ("I'm here to help! You can ask me about coding, request new features, "
                   "or get assistance with the code editor. AI integration is currently being enhanced "
                   "to provide more intelligent responses.")
        
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return ("Hello! I'm your AI assistant. Feel free to ask questions, "
                   "request features, or get help with your code. How can I assist you today?")
        
        else:
            return (f"I received your message: '{user_message}'. "
                   "AI integration is being enhanced to provide more intelligent responses. "
                   "For now, I can acknowledge your requests and they will be tracked in the system.")


# Create a singleton instance
ai_service = AIService()
