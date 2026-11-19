from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import Batch,AuditEvent

def is_teacher(user):
    return user.is_authenticated and (user.is_superuser or (user.is_staff and user.groups.filter(name='Teacher').exists()))

def teacher_required(view):
    @login_required
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if not is_teacher(request.user):raise PermissionDenied
        return view(request,*args,**kwargs)
    return wrapped

def batches_for(user):
    return Batch.objects.all() if user.is_superuser else Batch.objects.filter(teacher=user)

def audit(user,action,target,batch=None):
    AuditEvent.objects.create(actor=user,action=action,target=str(target)[:180],batch=batch)
