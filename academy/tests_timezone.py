from datetime import datetime, timezone as dt_timezone
from django.test import TestCase
from django.template import Template, Context
from django.utils import timezone
from django.contrib.auth.models import User
from learning.models import Subject, Concept, Question
from .models import Batch, Assessment
from .forms import AssessmentForm
from .portal_forms import AssignmentGeneratorForm


class BangladeshTimeTests(TestCase):
    def setUp(self):
        timezone.deactivate()
        self.teacher=User.objects.create_user('teacher')
        self.subject=Subject.objects.create(name='Python')
        self.concept=Concept.objects.create(subject=self.subject,name='Loops')
        self.batch=Batch.objects.create(name='Class',subject=self.subject,teacher=self.teacher)
        self.question=Question.objects.create(concept=self.concept,question_text='Question?',option_a='A',option_b='B',option_c='C',option_d='D',correct_answer='a')

    def test_assignment_form_converts_bd_input_to_utc(self):
        form=AssignmentGeneratorForm({'title':'Practice','concepts':[self.concept.pk],'difficulty':'easy',
            'opens_at':'2026-09-11T21:20','closes_at':'2026-09-12T21:20'},batch=self.batch)
        self.assertTrue(form.is_valid(),form.errors)
        self.assertEqual(form.cleaned_data['opens_at'].astimezone(dt_timezone.utc),datetime(2026,9,11,15,20,tzinfo=dt_timezone.utc))

    def test_edit_form_displays_existing_instant_in_bd_and_roundtrips(self):
        instant=datetime(2026,9,11,21,20,tzinfo=dt_timezone.utc)
        assessment=Assessment.objects.create(batch=self.batch,title='Exam',opens_at=instant,
            closes_at=datetime(2026,9,12,21,20,tzinfo=dt_timezone.utc))
        form=AssessmentForm(instance=assessment,batch=self.batch)
        self.assertIn('2026-09-12T03:20',str(form['opens_at']))
        data={'title':'Exam','kind':'exam','questions':[self.question.pk],'opens_at':'2026-09-12T03:20',
            'closes_at':'2026-09-13T03:20','duration_minutes':30,'max_attempts':1,'pass_percent':70}
        edited=AssessmentForm(data,instance=assessment,batch=self.batch)
        self.assertTrue(edited.is_valid(),edited.errors)
        edited.save();assessment.refresh_from_db()
        self.assertEqual(assessment.opens_at,instant)

    def test_template_converts_utc_date_without_changing_timestamp(self):
        instant=datetime(2026,9,11,21,20,tzinfo=dt_timezone.utc)
        result=Template('{{ value|date:"Y-m-d H:i" }}').render(Context({'value':instant}))
        self.assertEqual(result,'2026-09-12 03:20')
        self.assertEqual(instant.hour,21)
