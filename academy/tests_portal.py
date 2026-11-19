import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.test import TestCase, Client
from django.utils import timezone
from learning.models import Subject, Concept, Dependency, QuizAttempt, Question
from .models import Batch, Assessment, AssessmentAttempt, CourseCertificate, AuditEvent
from .completion import eligibility


class PortalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin=User.objects.create_superuser('admin','admin@example.com','test1234')
        self.teacher=User.objects.create_user('teacher',email='teacher@example.com',is_staff=True)
        group=Group.objects.create(name='Teacher');self.teacher.groups.add(group)
        self.student=User.objects.create_user('student',email='student@example.com')
        self.other=User.objects.create_user('other')
        self.subject=Subject.objects.create(name='Computer Science')
        self.concept=Concept.objects.create(subject=self.subject,name='Arrays')
        self.batch=Batch.objects.create(name='Batch A',subject=self.subject,teacher=self.teacher,completion_enabled=True)
        self.batch.students.add(self.student)
        self.assignment=Assessment.objects.create(batch=self.batch,title='Array assignment',kind='assignment',
            opens_at=timezone.now()-timedelta(days=2),closes_at=timezone.now()-timedelta(days=1),published=True,results_released=True)
        self.quiz=QuizAttempt.objects.create(user=self.student,concept=self.concept,questions=[],score=80,submitted_at=timezone.now())
        self.attempt=AssessmentAttempt.objects.create(student=self.student,assessment=self.assignment,number=1,
            pass_percent=70,expires_at=timezone.now(),score=90,submitted_at=timezone.now())
        self.client.force_login(self.admin)

    def test_admin_pages_render(self):
        for url in ['/manage/','/manage/accounts/','/manage/curriculum/',f'/manage/accounts/{self.student.pk}/',
                    '/manage/subjects/new/',f'/manage/subjects/{self.subject.pk}/concepts/new/',
                    f'/teach/classes/{self.batch.pk}/ai-assignment/','/teach/completion/']:
            self.assertEqual(self.client.get(url).status_code,200,url)

    def test_student_and_teacher_cannot_admin(self):
        for user in [self.student,self.teacher]:
            self.client.force_login(user)
            self.assertEqual(self.client.get('/manage/').status_code,403)
            self.assertEqual(self.client.post(f'/manage/accounts/{self.other.pk}/',{'is_superuser':'on'}).status_code,403)

    def test_superuser_protected_and_teacher_reassignment_required(self):
        self.client.post(f'/manage/accounts/{self.admin.pk}/',{'role':'student'})
        self.admin.refresh_from_db();self.assertTrue(self.admin.is_superuser)
        self.client.post(f'/manage/accounts/{self.teacher.pk}/',{'email':self.teacher.email,'role':'student','is_active':'on'})
        self.teacher.refresh_from_db();self.assertTrue(self.teacher.is_staff)

    def test_role_update_audited(self):
        self.client.post(f'/manage/accounts/{self.other.pk}/',{'email':'other@example.com','role':'teacher','is_active':'on','is_superuser':'on'})
        self.other.refresh_from_db();self.assertTrue(self.other.is_staff);self.assertFalse(self.other.is_superuser)
        self.assertTrue(self.other.groups.filter(name='Teacher').exists())
        self.assertTrue(AuditEvent.objects.filter(action='account.updated').exists())

    def test_cycle_rejected(self):
        child=Concept.objects.create(subject=self.subject,name='Sorting')
        Dependency.objects.create(concept=child,prerequisite=self.concept)
        self.client.post(f'/manage/subjects/{self.subject.pk}/concepts/{self.concept.pk}/',{'name':'Arrays','prerequisites':[child.pk]})
        self.assertFalse(Dependency.objects.filter(concept=self.concept).exists())

    def test_weighted_score_and_latest_attempt(self):
        self.assertEqual(eligibility(self.student,self.batch)['score'],Decimal('86.00'))
        QuizAttempt.objects.create(user=self.student,concept=self.concept,questions=[],score=10,submitted_at=timezone.now())
        self.assertFalse(eligibility(self.student,self.batch)['eligible'])

    def test_missing_concept_and_unreleased_block(self):
        self.assignment.results_released=False;self.assignment.save()
        status=eligibility(self.student,self.batch)
        self.assertFalse(status['eligible']);self.assertEqual(status['assignment_score'],0)
        self.assignment.results_released=True;self.assignment.save()
        Concept.objects.create(subject=self.subject,name='Loops')
        self.assertFalse(eligibility(self.student,self.batch)['eligible'])

    def issue(self):
        self.client.force_login(self.student)
        return self.client.post(f'/completion/{self.batch.pk}/issue/',{'name':'Test Student','consent':'yes','score':100})

    def test_certificate_snapshot_pdf_and_public_privacy(self):
        self.assertEqual(self.issue().status_code,302)
        cert=CourseCertificate.objects.get();self.assertEqual(cert.score,Decimal('86'))
        self.assertEqual(cert.evidence['quiz_attempts'],[self.quiz.pk])
        response=self.client.get(f'/completion/certificates/{cert.pk}/download/')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.quiz.score=0;self.quiz.save();self.issue()
        self.assertEqual(CourseCertificate.objects.count(),1)
        cert.refresh_from_db();self.assertEqual(cert.score,Decimal('86'))
        self.client.logout();response=self.client.get(f'/completion/certificates/{cert.pk}/verify/')
        self.assertContains(response,'Test Student');self.assertNotContains(response,self.student.email)

    def test_certificate_access_and_revocation(self):
        self.issue();cert=CourseCertificate.objects.get()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/completion/certificates/{cert.pk}/download/').status_code,403)
        self.assertEqual(self.client.post(f'/completion/{self.batch.pk}/issue/').status_code,404)
        self.client.force_login(self.teacher)
        self.client.post(f'/teach/completion/{cert.pk}/revoke/',{'reason':'Correction'})
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(f'/completion/certificates/{cert.pk}/download/').status_code,410)

    def test_consent_and_policy_required(self):
        self.client.force_login(self.student)
        self.client.post(f'/completion/{self.batch.pk}/issue/',{'name':'Test Student'})
        self.assertFalse(CourseCertificate.objects.exists())
        self.batch.completion_enabled=False;self.batch.save()
        self.assertEqual(self.issue().status_code,403)

    def test_completion_page(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/completion/'),'86.00')

    def generator_payload(self):
        return {'title':'Generated work','concepts':[self.concept.pk],'difficulty':'easy',
            'opens_at':'2027-01-01T10:00','closes_at':'2027-01-02T10:00'}

    @patch('learning.ai_engine._call_json')
    def test_assignment_draft_requires_review(self,mock):
        mock.return_value=json.dumps([{'question':f'Question {i}?','option_a':'A','option_b':'B','option_c':'C','option_d':'D','correct_answer':'a','explanation':'Because A.'} for i in range(5)])
        response=self.client.post(f'/teach/classes/{self.batch.pk}/ai-assignment/',self.generator_payload())
        self.assertEqual(response.status_code,302)
        draft=Assessment.objects.get(title='Generated work');self.assertFalse(draft.published)
        self.assertEqual(draft.questions.filter(approval_status='pending').count(),5)
        self.client.post(f'/teach/assessments/{draft.pk}/action/',{'action':'publish'})
        draft.refresh_from_db();self.assertFalse(draft.published)

    @patch('learning.ai_engine._call_json',return_value='[{"question":"incomplete"}]')
    def test_bad_ai_saves_nothing(self,mock):
        self.client.post(f'/teach/classes/{self.batch.pk}/ai-assignment/',self.generator_payload())
        self.assertEqual(Assessment.objects.count(),1);self.assertFalse(Question.objects.exists())

    @patch('learning.ai_engine._call_json')
    def test_generation_denied_to_student(self,mock):
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(f'/teach/classes/{self.batch.pk}/ai-assignment/',self.generator_payload()).status_code,403)
        mock.assert_not_called()

    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.admin)
        self.assertEqual(client.post('/manage/subjects/new/',{'name':'Attack'}).status_code,403)

    def test_question_edit_resets_approval_and_blocks_published(self):
        question=Question.objects.create(concept=self.concept,question_text='Old?',option_a='A',option_b='B',option_c='C',option_d='D',correct_answer='a')
        body={'question_text':'Revised?','option_a':'A','option_b':'B','option_c':'C','option_d':'D','correct_answer':'b','difficulty':'easy','explanation':'B is correct.'}
        self.assertEqual(self.client.post(f'/teach/questions/{question.pk}/edit/',body).status_code,302)
        question.refresh_from_db();self.assertEqual(question.approval_status,'pending');self.assertEqual(question.correct_answer,'b')
        self.assignment.questions.add(question)
        self.client.post(f'/teach/questions/{question.pk}/edit/',dict(body,correct_answer='c'))
        question.refresh_from_db();self.assertEqual(question.correct_answer,'b')
