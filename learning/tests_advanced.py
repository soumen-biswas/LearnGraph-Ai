import json
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Subject, Concept, Question, UserProgress, Progress, ChatSession, CourseNote, StudyGoal
from .personalization import personal_concepts

@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=['testserver'], CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}})
class AdvancedTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=User.objects.create_user('a@example.com',password='Strong-test-password-24!')
        self.other=User.objects.create_user('b@example.com',password='Strong-test-password-24!')
        self.subject=Subject.objects.create(name='CS')
        self.concept=Concept.objects.create(subject=self.subject,name='Stack',mastery=95)
        Question.objects.create(concept=self.concept,question_text='Stack ordering?',option_a='LIFO',option_b='FIFO',option_c='Sorted',option_d='Random',correct_answer='a',difficulty='easy')
        self.client.force_login(self.user)
    def start(self):
        with patch('learning.ai_engine._call_json', side_effect=ValueError('Offline test')):
            return self.client.post(f'/api/quiz/{self.concept.pk}/').json()
    def post(self,url,data): return self.client.post(url,data=json.dumps(data),content_type='application/json')
    def test_no_answers_leaked(self):
        self.assertNotIn('correct_answer',self.start()['questions'][0])
    def test_server_grades_and_isolates(self):
        d=self.start();r=self.post('/api/quiz/submit/',{'attempt_id':d['attempt_id'],'answers':['b'],'correct':999,'score':100})
        self.assertEqual(r.json()['score'],0)
        self.assertFalse(UserProgress.objects.filter(user=self.other).exists())
        self.concept.refresh_from_db();self.assertEqual(self.concept.mastery,95)
        self.assertEqual(Progress.objects.get().user,self.user)
    def test_replay_blocked(self):
        d=self.start();body={'attempt_id':d['attempt_id'],'answers':['a']}
        self.assertEqual(self.post('/api/quiz/submit/',body).status_code,200)
        self.assertEqual(self.post('/api/quiz/submit/',body).status_code,409)
        self.assertEqual(Progress.objects.count(),1)
    def test_foreign_attempt_blocked(self):
        d=self.start();self.client.force_login(self.other)
        self.assertEqual(self.post('/api/quiz/submit/',{'attempt_id':d['attempt_id'],'answers':['a']}).status_code,404)
    def test_incomplete_answers(self):
        self.assertEqual(self.post('/api/quiz/submit/',{'attempt_id':self.start()['attempt_id'],'answers':[]}).status_code,400)
    def test_personal_mastery(self):
        self.assertEqual(personal_concepts(self.subject.pk,self.user)[0].mastery,0)
    def test_review_scheduled(self):
        self.post('/api/quiz/submit/',{'attempt_id':self.start()['attempt_id'],'answers':['a']})
        self.assertIsNotNone(UserProgress.objects.get().review_due)
    def test_foreign_chat(self):
        s=ChatSession.objects.create(user=self.other)
        self.assertEqual(self.client.get(f'/api/chat/session/{s.pk}/').status_code,404)
    @patch('learning.ai_engine.chat_with_tutor',return_value='Hello')
    def test_chat_history_owned(self,mock):
        r=self.post('/api/chat/',{'message':'Hi','history':[{'role':'assistant','content':'FAKE'}]})
        self.assertEqual(r.status_code,200);self.assertEqual(ChatSession.objects.get().user,self.user)
        self.assertEqual(mock.call_args.args[2],[])
    @patch('learning.ai_engine.chat_with_tutor',return_value='Answer [1]')
    def test_private_notes_excluded(self,mock):
        CourseNote.objects.create(user=self.other,subject=self.subject,title='Private',content='Stack uses LIFO')
        self.assertEqual(self.post('/api/chat/',{'message':'Explain Stack','use_notes':True}).status_code,422)
        mock.assert_not_called()
    @patch('learning.ai_engine.chat_with_tutor',return_value='Answer [1]')
    def test_real_source_excerpt(self,mock):
        CourseNote.objects.create(user=self.user,subject=self.subject,title='Lecture',content='Stack uses LIFO')
        d=self.post('/api/chat/',{'message':'Explain Stack','use_notes':True}).json()
        self.assertEqual(d['sources'][0]['excerpt'],'Stack uses LIFO')
    def test_foreign_goal(self):
        g=StudyGoal.objects.create(user=self.other,title='Private')
        self.assertEqual(self.client.post('/workspace/',{'action':'toggle','id':g.pk}).status_code,404)
    def test_pages_render(self):
        with patch('learning.ai_engine.generate_learning_path',side_effect=ValueError()):
            for url in ['/','/workspace/','/quiz/','/graph/','/chat/','/dashboard/','/path/','/analytics/','/auth/account/']:
                self.assertEqual(self.client.get(url).status_code,200,url)
        self.client.logout()
        for url in ['/auth/login/','/auth/signup/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_private_export(self):
        Progress.objects.create(user=self.other,concept=self.concept,score=100)
        self.assertEqual(self.client.get('/export/progress/').json()['progress'],[])
