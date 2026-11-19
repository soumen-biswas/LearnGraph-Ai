from django.contrib import admin
from .models import Subject, Concept, Dependency, Question, Progress, UserProfile, UserProgress

admin.site.site_header = 'LearnGraph Administration'
admin.site.site_title = 'LearnGraph Admin'
admin.site.index_title = 'Learning content and accounts'

class AuditedAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request,obj,form,change)
        from academy.access import audit
        audit(request.user,'admin.updated' if change else 'admin.created',f'{obj._meta.label}:{obj.pk}')
    def delete_model(self, request, obj):
        from academy.access import audit
        audit(request.user,'admin.deleted',f'{obj._meta.label}:{obj.pk}')
        super().delete_model(request,obj)
    def delete_queryset(self, request, queryset):
        from academy.access import audit
        audit(request.user,'admin.bulk_deleted',f'{queryset.model._meta.label}: {queryset.count()} records')
        super().delete_queryset(request,queryset)

@admin.register(Subject)
class SubjectAdmin(AuditedAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Concept)
class ConceptAdmin(AuditedAdmin):
    list_display = ('name', 'subject', 'mastery')
    list_filter = ('subject',)
    search_fields = ('name',)

@admin.register(Question)
class QuestionAdmin(AuditedAdmin):
    list_display = ('question_text', 'concept', 'difficulty', 'approval_status', 'ai_generated')
    search_fields = ('question_text', 'concept__name')
    list_filter = ('approval_status', 'difficulty', 'ai_generated', 'concept__subject')
    list_select_related = ('concept',)

admin.site.register([Dependency, Progress, UserProfile, UserProgress], AuditedAdmin)
# Verification codes deliberately excluded from the admin UI.

from .models import CourseNote, StudyGoal, ChatSession, QuizAttempt

@admin.register(CourseNote)
class CourseNoteAdmin(AuditedAdmin):
    list_display = ('title', 'subject', 'published')
    list_filter = ('subject', 'published')
    search_fields = ('title',)
    exclude = ('user',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(user=request.user)
    def save_model(self, request, obj, form, change):
        if not change: obj.user = request.user
        super().save_model(request, obj, form, change)
# Private chats are intentionally not registered in admin.
