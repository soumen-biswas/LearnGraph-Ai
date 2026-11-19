"""Safe diagnostics: never include provider bodies or credentials."""
import logging

def explain_error(exc):
    name = type(exc).__name__
    status = getattr(exc, 'status_code', None)
    logging.getLogger(__name__).warning('AI request failed: type=%s status=%s', name, status if isinstance(status, int) else 'unknown')
    if name == 'AIConfigurationError':
        return 'AI is not configured. Ask the administrator to check the Groq key.'
    if status in (401, 403):
        return 'AI access was rejected. The administrator needs to check the API key and permissions.'
    if status == 429:
        return 'AI usage limit reached. Please wait and try again.'
    if status in (400, 404):
        return 'The AI model or request is unavailable. Ask the administrator to run check_ai.'
    if name in ('APIConnectionError', 'APITimeoutError', 'TimeoutError'):
        return 'Cannot reach the AI service. Check the server connection and try again.'
    return 'AI could not complete this request. Please retry or ask the administrator to run check_ai.'
