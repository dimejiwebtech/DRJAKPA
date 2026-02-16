from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import ChatSession, ChatMessage
from .services import JakpaChatbot


chatbot = JakpaChatbot()


@csrf_exempt
@require_http_methods(["POST"])
def initialize_session(request):
    try:
        session = ChatSession.objects.create()
        greeting = chatbot.get_greeting()
        
        # Store greeting message
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=greeting
        )
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.session_id),
            'greeting': greeting,
            'expires_at': session.expires_at.isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()
        
        if not session_id or not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Missing session_id or message'
            }, status=400)
        
        # Get session
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found or expired'
            }, status=404)
        
        # Check if session expired
        if session.is_expired():
            session.is_active = False
            session.save()
            return JsonResponse({
                'success': False,
                'error': 'Session expired',
                'expired': True
            }, status=403)
        
        # Store user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )
        
        # Get conversation history
        previous_messages = list(session.messages.values('role', 'content').order_by('timestamp'))
        conversation_history = previous_messages[1:-1]  # Exclude greeting and current message
        
        # Generate AI response
        ai_response = chatbot.generate_response(user_message, conversation_history)
        
        # Store AI response
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_chat_history(request, session_id):
    try:
        session = ChatSession.objects.get(session_id=session_id)
        
        if session.is_expired():
            return JsonResponse({
                'success': False,
                'error': 'Session expired',
                'expired': True
            }, status=403)
        
        messages = list(session.messages.values('role', 'content', 'timestamp').order_by('timestamp'))
        
        return JsonResponse({
            'success': True,
            'messages': messages,
            'expires_at': session.expires_at.isoformat()
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def chat(request):
    """Simple view for testing - not used in production"""
    return JsonResponse({'message': 'Jakpa Bot API is running'})
