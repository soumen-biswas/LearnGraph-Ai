from .models import Subject


def global_context(request):
    """
    Inject subjects + active_subject into every template automatically.
    Add 'learning.context_processors.global_context' to TEMPLATES OPTIONS.
    """
    subjects = Subject.objects.all()

    active_subject_id = request.session.get('active_subject_id')
    active_subject = None
    if active_subject_id:
        active_subject = subjects.filter(id=active_subject_id).first()
    if not active_subject:
        active_subject = subjects.first()

    from academy.access import is_teacher
    return {
        'is_teacher': is_teacher(request.user),
        'subjects': subjects,
        'active_subject': active_subject,
    }
