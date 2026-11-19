import csv,io,json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth.models import User,Group
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,Client
from django.utils import timezone
from learning.models import Subject,Concept,Question
from .models import Batch,Assessment,AssessmentAttempt,Certificate,AuditEvent,AIUsage
from .services import CSV_FIELDS

class AcademyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.teacher=User.objects.create_user('teacher',email='teacher@example.com',is_staff=True)
        self.other=User.objects.create_user('other',email='other@example.com',is_staff=True)
        group=Group.objects.create(name='Teacher');self.teacher.groups.add(group);self.other.groups.add(group)
        self.student=User.objects.create_user('student',email='student@example.com')
        self.outsider=User.objects.create_user('outsider',email='outsider@example.com')
        self.admin=User.objects.create_superuser('admin','admin@example.com','Secret123!')
        self.subject=Subject.objects.create(name='Data Structures')
        self.concept=Concept.objects.create(subject=self.subject,name='Stack')
        self.question=Question.objects.create(concept=self.concept,question_text='Which ordering rule?',option_a='LIFO',option_b='FIFO',option_c='Sorted',option_d='Random',correct_answer='a',explanation='The most recently added item is removed first.')
        self.batch=Batch.objects.create(name='CSE 12',teacher=self.teacher,subject=self.subject);self.batch.students.add(self.student)
        self.exam=Assessment.objects.create(batch=self.batch,title='Data Structures Foundations',opens_at=timezone.now()-timedelta(minutes=2),closes_at=timezone.now()+timedelta(hours=1),duration_minutes=30,max_attempts=1,published=True,certificate_enabled=True)
        self.exam.questions.add(self.question);self.client.force_login(self.teacher)
    def start(self):
        self.client.force_login(self.student);self.client.post(f'/assessments/{self.exam.pk}/start/');return AssessmentAttempt.objects.get()
    def save(self,a,answers,submit=True):return self.client.post(f'/attempts/{a.pk}/save/',json.dumps({'answers':answers,'submit':submit,'score':100}),content_type='application/json')
    def release(self):self.exam.closes_at=timezone.now()-timedelta(seconds=1);self.exam.results_released=True;self.exam.save()
    def certificate(self):
        a=self.start();self.save(a,['a']);self.release();self.client.post(f'/attempts/{a.pk}/certificate/',{'name':'Soumen Biswas','consent':'yes'});return Certificate.objects.get()
    def test_cross_teacher_class_hidden(self):
        self.client.force_login(self.other);self.assertEqual(self.client.get(f'/teach/classes/{self.batch.pk}/').status_code,404)
    def test_cross_teacher_student_hidden(self):
        self.client.force_login(self.other);self.assertEqual(self.client.get(f'/teach/classes/{self.batch.pk}/students/{self.student.pk}/').status_code,404)
    def test_student_cannot_teach(self):
        self.client.force_login(self.student);self.assertEqual(self.client.get('/teach/').status_code,403)
    def test_enrollment_audited(self):
        self.client.post(f'/teach/classes/{self.batch.pk}/',{'email':self.outsider.email});self.assertTrue(self.batch.students.filter(pk=self.outsider.pk).exists());self.assertTrue(AuditEvent.objects.filter(action='student.enrolled').exists())
    def test_approval_recorded(self):
        self.question.approval_status='pending';self.question.save();self.client.post(f'/teach/questions/{self.question.pk}/review/',{'decision':'approved'});self.question.refresh_from_db();self.assertEqual(self.question.reviewed_by,self.teacher)
    def test_outsider_cannot_start(self):
        self.client.force_login(self.outsider);self.assertEqual(self.client.post(f'/assessments/{self.exam.pk}/start/').status_code,404)
    def test_pending_question_blocks_start(self):
        self.question.approval_status='pending';self.question.save();self.client.force_login(self.student);self.client.post(f'/assessments/{self.exam.pk}/start/');self.assertFalse(AssessmentAttempt.objects.exists())
    def test_answer_explanations_hidden_during_exam(self):
        a=self.start();self.assertNotContains(self.client.get(f'/attempts/{a.pk}/'),'The most recently added item is removed first.')
    def test_score_computed_on_server(self):
        a=self.start();self.save(a,['b']);a.refresh_from_db();self.assertEqual(a.score,0)
    def test_replay_blocked(self):
        a=self.start();self.save(a,['a']);self.assertEqual(self.save(a,['b']).status_code,409);a.refresh_from_db();self.assertEqual(a.score,100)
    def test_foreign_attempt_blocked(self):
        a=self.start();self.client.force_login(self.outsider);self.assertEqual(self.save(a,['a']).status_code,404)
    def test_attempt_limit(self):
        a=self.start();self.save(a,['a']);self.client.post(f'/assessments/{self.exam.pk}/start/');self.assertEqual(AssessmentAttempt.objects.count(),1)
    def test_deadline_enforced(self):
        a=self.start();self.save(a,['b'],False);a.expires_at=timezone.now()-timedelta(seconds=1);a.save();self.assertEqual(self.save(a,['a']).status_code,409);a.refresh_from_db();self.assertEqual(a.score,0)
    def test_results_hidden_until_release(self):
        a=self.start();self.save(a,['a']);r=self.client.get(f'/attempts/{a.pk}/result/');self.assertNotContains(r,'<strong>100%</strong>',html=True);self.assertContains(r,'teacher will release')
    def test_early_release_blocked(self):
        self.client.post(f'/teach/assessments/{self.exam.pk}/action/',{'action':'release'});self.exam.refresh_from_db();self.assertFalse(self.exam.results_released)
    def test_failing_result_cannot_certify(self):
        a=self.start();self.save(a,['b']);self.release();self.assertEqual(self.client.post(f'/attempts/{a.pk}/certificate/',{'name':'Test Name','consent':'yes'}).status_code,403)
    def test_certificate_pdf_and_public_verification(self):
        cert=self.certificate();r=self.client.get(f'/certificates/{cert.pk}/download/');self.assertEqual(r.status_code,200);self.assertTrue(r.content.startswith(b'%PDF'));self.client.logout();r=self.client.get(f'/certificates/{cert.pk}/verify/');self.assertContains(r,'Soumen Biswas');self.assertNotContains(r,'student@example.com')
    def test_certificate_owner_only(self):
        cert=self.certificate();self.client.force_login(self.outsider);self.assertEqual(self.client.get(f'/certificates/{cert.pk}/download/').status_code,403)
    def test_revocation_enforced(self):
        cert=self.certificate();self.client.force_login(self.teacher);self.client.post(f'/teach/certificates/{cert.pk}/revoke/',{'reason':'Issued in error'});self.client.force_login(self.student);self.assertEqual(self.client.get(f'/certificates/{cert.pk}/download/').status_code,410);self.assertContains(self.client.get(f'/certificates/{cert.pk}/verify/'),'Certificate revoked')
    def test_reports_scoped(self):
        a=self.start();self.save(a,['a']);self.client.force_login(self.other);self.assertNotContains(self.client.get('/teach/reports/?download=csv'),'student@example.com')
    def test_csv_formula_escape(self):
        a=self.start();self.save(a,['a']);self.student.first_name='=FORMULA';self.student.save();self.client.force_login(self.teacher);self.assertContains(self.client.get('/teach/reports/?download=csv'),"'=FORMULA")
    def test_import_atomic_and_pending(self):
        s=io.StringIO();w=csv.writer(s);w.writerow(CSV_FIELDS);w.writerow(['Stack','Question?','A','B','C','D','a','easy','Explanation'])
        r=self.client.post('/teach/questions/import/',{'subject':self.subject.pk,'file':SimpleUploadedFile('q.csv',s.getvalue().encode())});self.assertEqual(r.status_code,302);self.assertEqual(Question.objects.get(question_text='Question?').approval_status,'pending')
        w.writerow(['Missing','Invalid?','A','B','C','D','a','easy','']);before=Question.objects.count();self.client.post('/teach/questions/import/',{'subject':self.subject.pk,'file':SimpleUploadedFile('bad.csv',s.getvalue().encode())});self.assertEqual(Question.objects.count(),before)
    def test_usage_admin_only(self):
        self.assertEqual(self.client.get('/teach/usage/').status_code,403);self.client.force_login(self.admin);self.assertEqual(self.client.get('/teach/usage/').status_code,200)
    def test_provider_usage_logged(self):
        from learning.ai_engine import _call
        response=SimpleNamespace(usage=SimpleNamespace(prompt_tokens=12,completion_tokens=5),choices=[SimpleNamespace(message=SimpleNamespace(content='OK'))])
        with patch('learning.ai_engine._client') as c:c.return_value.chat.completions.create.return_value=response;self.assertEqual(_call('system','user'),'OK')
        self.assertEqual(AIUsage.objects.get().prompt_tokens,12)
    def test_csrf_submission(self):
        a=self.start();c=Client(enforce_csrf_checks=True);c.force_login(self.student);self.assertEqual(c.post(f'/attempts/{a.pk}/save/',data='{}',content_type='application/json').status_code,403)
    def test_pages_render(self):
        for url in ['/teach/','/teach/classes/new/',f'/teach/classes/{self.batch.pk}/',f'/teach/classes/{self.batch.pk}/students/{self.student.pk}/',f'/teach/classes/{self.batch.pk}/assessment/new/','/teach/questions/','/teach/questions/new/','/teach/questions/import/','/teach/reports/','/teach/audit/']:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_administrator_can_assign_class_owner(self):
        self.client.force_login(self.admin)
        self.client.post('/teach/classes/new/',{'name':'Assigned class','subject':self.subject.pk,'teacher':self.other.pk})
        self.assertEqual(Batch.objects.get(name='Assigned class').teacher,self.other)
    def test_form_does_not_allow_teacher_reassignment(self):
        self.client.post(f'/teach/classes/{self.batch.pk}/edit/',{'name':'Renamed','subject':self.subject.pk,'teacher':self.other.pk})
        self.batch.refresh_from_db();self.assertEqual(self.batch.teacher,self.teacher)
    def test_former_teacher_cannot_download_certificate(self):
        cert=self.certificate();self.teacher.is_staff=False;self.teacher.save();self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(f'/certificates/{cert.pk}/download/').status_code,403)
    def test_release_finalizes_expired_unsubmitted_attempt(self):
        a=self.start();self.save(a,['a'],False);self.exam.closes_at=timezone.now()-timedelta(seconds=1);self.exam.save();self.client.force_login(self.teacher)
        self.client.post(f'/teach/assessments/{self.exam.pk}/action/',{'action':'release'})
        a.refresh_from_db();self.assertIsNotNone(a.submitted_at);self.assertEqual(a.score,100)
    def test_teacher_account_delete_handles_owned_class(self):
        self.teacher.set_password('Long-safe-password-123!');self.teacher.save();self.client.force_login(self.teacher)
        r=self.client.post('/auth/delete/',{'password':'Long-safe-password-123!','confirm':'DELETE'})
        self.assertEqual(r.status_code,200);self.assertContains(r,'reassign');self.assertTrue(User.objects.filter(pk=self.teacher.pk).exists())
