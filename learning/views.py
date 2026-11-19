from .personalization import personal_concepts, mastery_for
import json
from .ai_errors import explain_error
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .models import Subject, Concept, Dependency, Progress
from . import graph_engine, quiz_engine, path_engine, analytics_engine, missing_engine, ai_engine


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_subjects():
    return Subject.objects.all()

def get_active_subject(request):
    subject_id = request.session.get('active_subject_id')
    if subject_id:
        try:
            return Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            pass
    return Subject.objects.first()


# ── HOME ──────────────────────────────────────────────────────────────────────
@login_required
def home(request):
    from academy.access import is_teacher
    if request.user.is_superuser:
        return redirect('portal_home')
    if is_teacher(request.user):
        return redirect('academy_dashboard')
    subjects = Subject.objects.all()
    subject_data = []
    for s in subjects:
        concepts = personal_concepts(s.pk, request.user)
        avg = round(sum(c.mastery for c in concepts) / len(concepts)) if bool(concepts) else 0
        subject_data.append({'subject': s, 'avg_mastery': avg, 'concept_count': len(concepts)})

    return render(request, 'learning/home.html', {
        'subject_data': subject_data,
        'subjects': subjects,
        'active_subject': get_active_subject(request),
        'page': 'home',
    })


@login_required
def set_subject(request, subject_id):
    request.session['active_subject_id'] = subject_id
    next_url = request.GET.get('next', '/')
    return redirect(next_url if url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()) else '/')


# ── GRAPH ─────────────────────────────────────────────────────────────────────
@login_required
def graph_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    if not subject:
        return redirect('home')

    graph_data = graph_engine.get_graph_data(subject.id, request.user)
    missing = missing_engine.detect_missing_concepts(subject.id, request.user)

    return render(request, 'learning/graph.html', {
        'subject': subject,
        'subjects': subjects,
        'graph_data_json': json.dumps(graph_data),
        'missing': missing,
        'page': 'graph',
    })


@login_required
def api_graph_data(request, subject_id):
    data = graph_engine.get_graph_data(subject_id, request.user)
    return JsonResponse(data)


@login_required
def api_update_position(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if not request.user.is_staff:
            return JsonResponse({'ok': True})  # Student graph positions are temporary.
        graph_engine.update_concept_position(data['id'], data['x'], data['y'])
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'POST required'}, status=405)


# ── QUIZ ──────────────────────────────────────────────────────────────────────
@login_required
def quiz_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    concepts = personal_concepts(subject.pk, request.user) if subject else []
    return render(request, 'learning/quiz.html', {
        'subject': subject,
        'subjects': subjects,
        'concepts': concepts,
        'page': 'quiz',
    })


@login_required
@require_http_methods(['POST'])
def api_refresh_quiz(request, concept_id):
    """Force regenerate quiz bank for a concept."""
    from academy.access import is_teacher, batches_for
    if not is_teacher(request.user) or not Concept.objects.filter(pk=concept_id, subject_id__in=batches_for(request.user).values_list('subject_id', flat=True)).exists():
        return JsonResponse({'error': 'Only the class teacher can request a new question bank.'}, status=403)
    try:
        saved = quiz_engine.refresh_quiz_bank(concept_id)
        from .advanced import quiz_start
        return quiz_start(request, concept_id)
    except Exception as e:
        return JsonResponse({'error': explain_error(e)}, status=500)


# ── CHATBOT ───────────────────────────────────────────────────────────────────
@login_required
def chatbot_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    return render(request, 'learning/chatbot.html', {
        'subject': subject,
        'subjects': subjects,
        'page': 'chat',
    })


# ── LEARNING PATH ─────────────────────────────────────────────────────────────
@login_required
def path_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    path_data = None
    if subject:
        path_data = path_engine.get_learning_path(subject.id, request.user, use_ai=False)
    return render(request, 'learning/path.html', {
        'subject': subject,
        'subjects': subjects,
        'path_data': path_data,
        'path_data_json': json.dumps(path_data) if path_data else 'null',
        'page': 'path',
    })


@login_required
def api_generate_path(request, subject_id):
    try:
        data = path_engine.get_learning_path(subject_id, request.user)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': explain_error(e)}, status=500)


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@login_required
def dashboard_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    dashboard_data = None
    if subject:
        dashboard_data = analytics_engine.get_dashboard_data(subject.id, request.user)
    return render(request, 'learning/dashboard.html', {
        'subject': subject,
        'subjects': subjects,
        'dashboard': dashboard_data,
        'dashboard_json': json.dumps(dashboard_data, default=str) if dashboard_data else 'null',
        'page': 'dashboard',
    })


# ── ANALYTICS ─────────────────────────────────────────────────────────────────
@login_required
def analytics_view(request):
    subject = get_active_subject(request)
    subjects = get_subjects()
    return render(request, 'learning/analytics.html', {
        'subject': subject,
        'subjects': subjects,
        'page': 'analytics',
    })


@login_required
def api_get_analytics(request, subject_id):
    try:
        data = analytics_engine.get_ai_analytics(subject_id, request.user)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': explain_error(e)}, status=500)


# ── LEARNING SUGGESTION ───────────────────────────────────────────────────────
@login_required
def api_get_suggestion(request, concept_id):
    try:
        concept = Concept.objects.get(id=concept_id)
        data = ai_engine.get_learning_suggestion(concept.name, mastery_for(request.user, concept))
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': explain_error(e)}, status=500)


@login_required
def api_get_suggestion_by_name(request):
    """Suggestion lookup by concept name + subject_id."""
    name = request.GET.get('name', '')
    subject_id = request.GET.get('subject', None)
    try:
        qs = Concept.objects.filter(name__icontains=name)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        concept = qs.first()
        if not concept:
            return JsonResponse({'error': 'Concept not found'}, status=404)
        data = ai_engine.get_learning_suggestion(concept.name, mastery_for(request.user, concept))
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': explain_error(e)}, status=500)


@login_required
def api_path_redirect(request, subject_id):
    """Regenerate path and redirect back to path page."""
    # Clear cached path (if any) — just redirect; view will regenerate
    return redirect('path')
