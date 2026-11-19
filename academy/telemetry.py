from contextvars import ContextVar
import time
current_user=ContextVar('current_actor',default=None)

class ActorMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        token=current_user.set(request.user if request.user.is_authenticated else None)
        try:return self.get_response(request)
        finally:current_user.reset(token)

def record_completion(call,model,operation):
    from .models import AIUsage
    started=time.monotonic();response=None;failure=None
    try:
        response=call();return response
    except Exception as exc:
        failure=type(exc).__name__;raise
    finally:
        usage=getattr(response,'usage',None)
        AIUsage.objects.create(user=current_user.get(),operation=operation,model=model,success=failure is None,error_type=failure or '',prompt_tokens=getattr(usage,'prompt_tokens',0) or 0,completion_tokens=getattr(usage,'completion_tokens',0) or 0,duration_ms=round((time.monotonic()-started)*1000))
