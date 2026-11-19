from django.urls import path
from django.contrib.auth import views as auth
from . import advanced
from . import views
from . import auth_views

urlpatterns = [
    path('auth/password-reset/', auth.PasswordResetView.as_view(template_name='learning/auth/reset_form.html', email_template_name='learning/auth/reset_email.txt', subject_template_name='learning/auth/reset_subject.txt'), name='password_reset'),
    path('auth/password-reset/sent/', auth.PasswordResetDoneView.as_view(template_name='learning/auth/reset_done.html'), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(template_name='learning/auth/reset_confirm.html'), name='password_reset_confirm'),
    path('auth/reset/complete/', auth.PasswordResetCompleteView.as_view(template_name='learning/auth/reset_complete.html'), name='password_reset_complete'),
    path('workspace/', advanced.workspace, name='workspace'),
    path('api/chat/session/<int:session_id>/', advanced.session_detail, name='chat_session'),
    path('export/progress/', advanced.export_progress, name='export_progress'),
    # ── AUTH ──────────────────────────────────────────────────────────────────
    path('auth/signup/', auth_views.signup_view, name='signup'),
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/verify/', auth_views.verify_email_view, name='verify_email'),
    path('auth/resend/', auth_views.resend_code_view, name='resend_code'),
    path('auth/account/', auth_views.account_view, name='account'),
    path('auth/delete/', auth_views.delete_account_view, name='delete_account'),

    # ── PAGES ─────────────────────────────────────────────────────────────────
    path('', views.home, name='home'),
    path('graph/', views.graph_view, name='graph'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('chat/', views.chatbot_view, name='chatbot'),
    path('path/', views.path_view, name='path'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('analytics/', views.analytics_view, name='analytics'),

    # ── SUBJECT SWITCHER ──────────────────────────────────────────────────────
    path('set-subject/<int:subject_id>/', views.set_subject, name='set_subject'),

    # ── JSON APIs ─────────────────────────────────────────────────────────────
    path('api/graph/<int:subject_id>/', views.api_graph_data, name='api_graph'),
    path('api/graph/position/', views.api_update_position, name='api_position'),
    path('api/quiz/<int:concept_id>/', advanced.quiz_start, name='api_quiz'),
    path('api/quiz/submit/', advanced.quiz_submit, name='api_submit_quiz'),
    path('api/quiz/refresh/<int:concept_id>/', views.api_refresh_quiz, name='api_refresh_quiz'),
    path('api/chat/', advanced.chat, name='api_chat'),
    path('api/path/<int:subject_id>/', views.api_generate_path, name='api_path'),
    path('api/analytics/<int:subject_id>/', views.api_get_analytics, name='api_analytics'),
    path('api/suggestion/<int:concept_id>/', views.api_get_suggestion, name='api_suggestion'),
    path('api/suggestion/by-name/', views.api_get_suggestion_by_name, name='api_suggestion_by_name'),
]
