"""Request limits without recording raw IPs, email addresses or request bodies."""
import hashlib
import json
import math
import time
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import get_token


class RequestSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        get_token(request)
        sensitive_auth = request.path in ('/admin/login/', '/auth/login/', '/auth/signup/', '/auth/verify/', '/auth/resend/', '/auth/password-reset/') and request.method == 'POST'
        api = request.path.startswith('/api/')
        if sensitive_auth or api or (request.path.startswith('/teach/questions/generate/') and request.method == 'POST'):
            # Do not trust spoofable X-Forwarded-For headers.
            identity = str(request.user.pk) if request.user.is_authenticated else (request.META.get('HTTP_X_REAL_IP', '') if settings.TRUST_PROXY else request.META.get('REMOTE_ADDR', ''))
            identities = [identity]
            if sensitive_auth:
                email = request.POST.get('email') or request.POST.get('username') or request.session.get('pending_verification_email')
                if email:
                    identities.append(email.strip().lower())
            period, limit = (600, 10) if sensitive_auth else (60, 30)
            for value in identities:
                digest = hashlib.sha256(value.encode()).hexdigest()
                key = f'limit:{request.path if sensitive_auth else "api"}:{digest}:{int(time.time()) // period}'
                if cache.add(key, 1, period):
                    count = 1
                else:
                    try:
                        count = cache.incr(key)
                    except ValueError:
                        return JsonResponse({'error': 'Please retry shortly.'}, status=429)
                if count > limit:
                    response = JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)
                    response['Retry-After'] = str(period)
                    return response
        if api and not request.user.is_authenticated:
            return JsonResponse({'error': 'Sign in required.'}, status=401)
        if request.user.is_authenticated and request.path.startswith(('/teach/questions/generate/', '/api/chat/', '/api/quiz/refresh/', '/api/path/', '/api/analytics/', '/api/suggestion/')) and '/session/' not in request.path:
            quota_key = f'ai-daily:{request.user.pk}:{int(time.time()) // 86400}'
            if cache.add(quota_key, 1, 86400):
                used = 1
            else:
                try: used = cache.incr(quota_key)
                except ValueError: used = 1
            if used > settings.AI_DAILY_REQUEST_LIMIT:
                return JsonResponse({'error':'Your daily AI request limit has been reached. Saved quizzes remain available.'}, status=429)
        if request.method == 'POST' and request.path in ('/api/chat/', '/api/quiz/submit/', '/api/graph/position/'):
            try:
                data = json.loads(request.body or b'{}')
                if not isinstance(data, dict):
                    raise ValueError()
                if request.path == '/api/chat/':
                    if not isinstance(data.get('message'), str) or not 1 <= len(data['message'].strip()) <= 8000:
                        raise ValueError()
                    if not isinstance(data.get('subject', ''), str) or len(data.get('subject', '')) > 200:
                        raise ValueError()
                    history = data.get('history', [])
                    if not isinstance(history, list) or len(history) > 20:
                        raise ValueError()
                    for item in history:
                        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant') or not isinstance(item.get('content'), str) or len(item['content']) > 8000:
                            raise ValueError()
                elif request.path == '/api/graph/position/':
                    if type(data.get('id')) is not int or any(type(data.get(k)) not in (int, float) or not math.isfinite(data[k]) or abs(data[k]) > 100000 for k in ('x', 'y')):
                        raise ValueError()
            except (ValueError, TypeError, UnicodeDecodeError):
                return JsonResponse({'error': 'Invalid request data.'}, status=400)
        return self.get_response(request)
