import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User,Group
from django.core.cache import cache
from django.test import TestCase,Client
from django.utils import timezone
from learning.models import Subject,Concept,QuizAttempt
from .models import Batch,ProjectAssignment,ProjectSubmission
from .completion import eligibility


class ProjectTests(TestCase):
    def setUp(self):
        cache.clear()
        self.teacher=User.objects.create_user('teacher',is_staff=True)
        self.other=User.objects.create_user('otherteacher',is_staff=True)
        group=Group.objects.create(name='Teacher');self.teacher.groups.add(group);self.other.groups.add(group)
        self.student=User.objects.create_user('student')
        self.outsider=User.objects.create_user('outsider')
        subject=Subject.objects.create(name='Python')
        self.concept=Concept.objects.create(subject=subject,name='Files')
        self.batch=Batch.objects.create(name='Class',subject=subject,teacher=self.teacher,completion_enabled=True)
        self.batch.students.add(self.student)
        self.project=ProjectAssignment.objects.create(batch=self.batch,title='Expense tracker',brief='Build a working expense tracker.',rubric='Functionality: 60\nTests: 40',
            opens_at=timezone.now()-timedelta(hours=1),closes_at=timezone.now()+timedelta(hours=1),published=True)
        self.client.force_login(self.student)
    def submit(self,**extra):
        return self.client.post(f'/projects/{self.project.pk}/',dict(response='My solution and tests',work_url='https://github.com/example/work',action='submit',**extra))
    def close(self):
        self.project.closes_at=timezone.now()-timedelta(seconds=1);self.project.save()
    def test_draft_final_and_replay(self):
        self.client.post(f'/projects/{self.project.pk}/',{'response':'Draft','action':'draft'})
        self.assertIsNone(ProjectSubmission.objects.get().submitted_at)
        self.submit(score=100);sub=ProjectSubmission.objects.get();self.assertIsNone(sub.score)
        self.submit();self.assertEqual(ProjectSubmission.objects.count(),1)
        sub.refresh_from_db();self.assertEqual(sub.response,'My solution and tests')
    def test_deadline_and_owner(self):
        self.close();self.submit();self.assertFalse(ProjectSubmission.objects.exists())
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(f'/projects/{self.project.pk}/').status_code,404)
    def test_unsafe_link_rejected(self):
        self.client.post(f'/projects/{self.project.pk}/',{'response':'Work','work_url':'javascript:alert(1)','action':'submit'})
        self.assertFalse(ProjectSubmission.objects.exists())
    def test_grading_access_and_release_gate(self):
        self.submit();sub=ProjectSubmission.objects.get()
        self.assertEqual(self.client.post(f'/teach/project-submissions/{sub.pk}/',{'score':100,'feedback':'Fake'}).status_code,403)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/teach/project-submissions/{sub.pk}/').status_code,404)
        self.client.force_login(self.teacher)
        self.close()
        self.client.post(f'/teach/projects/{self.project.pk}/action/',{'action':'release'})
        self.project.refresh_from_db();self.assertFalse(self.project.results_released)
        self.client.post(f'/teach/project-submissions/{sub.pk}/',{'score':85,'feedback':'Functionality 50, tests 35.'})
        sub.refresh_from_db();self.assertEqual(sub.score,85)
        self.client.post(f'/teach/projects/{self.project.pk}/action/',{'action':'release'})
        self.project.refresh_from_db();self.assertTrue(self.project.results_released)
        self.client.post(f'/teach/project-submissions/{sub.pk}/',{'score':100,'feedback':'Changed'})
        sub.refresh_from_db();self.assertEqual(sub.score,85)
    def test_project_contributes_only_after_release(self):
        self.submit();sub=ProjectSubmission.objects.get();sub.score=90;sub.feedback='Private marking';sub.reviewed_at=timezone.now();sub.save()
        QuizAttempt.objects.create(user=self.student,concept=self.concept,questions=[],score=80,submitted_at=timezone.now())
        self.assertFalse(eligibility(self.student,self.batch)['eligible'])
        self.assertNotContains(self.client.get(f'/projects/{self.project.pk}/'),'Private marking')
        self.project.results_released=True;self.project.save()
        result=eligibility(self.student,self.batch)
        self.assertTrue(result['eligible']);self.assertEqual(result['score'],Decimal('86.00'))
        self.assertEqual(result['evidence']['project_submissions'],[sub.pk])
    def test_published_brief_not_editable(self):
        self.client.force_login(self.teacher)
        self.client.post(f'/teach/projects/{self.project.pk}/edit/',{'title':'Changed'})
        self.project.refresh_from_db();self.assertEqual(self.project.title,'Expense tracker')
    def test_pages_render(self):
        self.assertContains(self.client.get('/assessments/'),'Expense tracker')
        self.assertEqual(self.client.get(f'/projects/{self.project.pk}/').status_code,200)
        self.submit();sub=ProjectSubmission.objects.get();self.client.force_login(self.teacher)
        for url in [f'/teach/projects/{self.project.pk}/',f'/teach/project-submissions/{sub.pk}/',f'/teach/classes/{self.batch.pk}/projects/new/',f'/teach/classes/{self.batch.pk}/projects/generate/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
    @patch('learning.ai_engine._call_json')
    def test_ai_draft_validation(self,mock):
        self.client.force_login(self.teacher)
        data={'title':'AI project','topic':'Expense tracker','difficulty':'beginner','opens_at':'2027-01-01T12:00','closes_at':'2027-01-05T12:00'}
        mock.return_value=json.dumps({'brief':'Implement a tracker with validation and file storage. '*5,'criteria':[{'name':'Functionality','marks':50},{'name':'Tests','marks':30},{'name':'Documentation','marks':20}]})
        self.client.post(f'/teach/classes/{self.batch.pk}/projects/generate/',data)
        project=ProjectAssignment.objects.get(title='AI project');self.assertFalse(project.published);self.assertTrue(project.ai_generated)
        mock.return_value='{"brief":"Invalid"}'
        self.client.post(f'/teach/classes/{self.batch.pk}/projects/generate/',dict(data,title='Bad'))
        self.assertFalse(ProjectAssignment.objects.filter(title='Bad').exists())
    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.student)
        self.assertEqual(client.post(f'/projects/{self.project.pk}/',{'response':'Work'}).status_code,403)
