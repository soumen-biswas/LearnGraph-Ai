from django.contrib import admin
from .models import Batch,Assessment,AssessmentAttempt,Certificate,AuditEvent,AIUsage

@admin.register(AuditEvent,AIUsage,AssessmentAttempt,Certificate)
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
    def has_view_permission(self,request,obj=None):return request.user.is_superuser
# Class and assessment writes use the scoped teaching portal, including validation and audit.
