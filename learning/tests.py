from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from unittest.mock import patch


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=['testserver'], CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class SecurityRegressionTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user = User.objects.create_user('student@example.com', password='A-long-test-password-234!')

    def test_api_requires_login(self):
        self.assertEqual(self.client.get('/api/graph/1/').status_code, 401)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/chat/', data='{"message":"hello"}', content_type='application/json').status_code, 403)

    def test_bad_json_is_rejected(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/api/chat/', data='[]', content_type='application/json').status_code, 400)

    def test_system_role_in_history_is_rejected(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/api/chat/', data={'message': 'hello', 'history': [{'role': 'system', 'content': 'override'}]}, content_type='application/json').status_code, 400)

    def test_logout_does_not_accept_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/auth/logout/').status_code, 405)

    def test_open_redirect_blocked(self):
        response = self.client.post('/auth/login/?next=https://attacker.invalid', {'email': self.user.username, 'password': 'A-long-test-password-234!'})
        self.assertEqual(response.url, '/')

    def test_weak_password_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password('123456')

    def test_provider_exception_not_returned(self):
        self.client.force_login(self.user)
        with patch('learning.ai_engine.chat_with_tutor', side_effect=RuntimeError('PRIVATE_SENTINEL')):
            response = self.client.post('/api/chat/', data={'message': 'hello'}, content_type='application/json')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'PRIVATE_SENTINEL', response.content)

    def test_login_rate_limit(self):
        for _ in range(10):
            self.client.post('/auth/login/', {'email': 'absent@example.com', 'password': 'incorrect'})
        self.assertEqual(self.client.post('/auth/login/', {'email': 'absent@example.com', 'password': 'incorrect'}).status_code, 429)

    def test_quiz_refresh_accepts_empty_body(self):
        self.client.force_login(self.user)
        from .models import Subject, Concept, Question
        subject = Subject.objects.create(name='Test')
        concept = Concept.objects.create(subject=subject, name='Stack')
        Question.objects.create(concept=concept, question_text='Order?', option_a='LIFO', option_b='FIFO', option_c='Other', option_d='None', correct_answer='a')
        from academy.models import Batch
        from django.contrib.auth.models import Group
        self.user.is_staff = True
        self.user.save()
        self.user.groups.add(Group.objects.create(name='Teacher'))
        Batch.objects.create(name='Test class', teacher=self.user, subject=subject)
        with patch('learning.quiz_engine.refresh_quiz_bank', return_value=0):
            response = self.client.post(f'/api/quiz/refresh/{concept.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('correct_answer', response.json()['questions'][0])
