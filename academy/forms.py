from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ValidationError
from learning.models import Subject,Question
from .models import Batch,Assessment

class BatchForm(forms.ModelForm):
    class Meta:model=Batch;fields=['name','subject','teacher']
    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        if user.is_superuser:
            self.fields['teacher'].queryset=User.objects.filter(is_active=True,is_staff=True).filter(Q(groups__name='Teacher')|Q(is_superuser=True)).distinct()
            if not self.instance.pk:self.fields['teacher'].initial=user.pk
        else:self.fields.pop('teacher')
        if self.instance.pk:self.fields['subject'].disabled=True


class EnrollmentForm(forms.Form):
    email=forms.EmailField(label='Student account email',max_length=150)

class AssessmentForm(forms.ModelForm):
    class Meta:
        model=Assessment
        fields=['title','kind','instructions','questions','opens_at','closes_at','duration_minutes','max_attempts','pass_percent','certificate_enabled']
        widgets={'opens_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type':'datetime-local'}),'closes_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type':'datetime-local'}),'questions':forms.CheckboxSelectMultiple()}
    def __init__(self,*args,batch,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['questions'].queryset=Question.objects.filter(concept__subject=batch.subject,approval_status='approved').select_related('concept')
        self.fields['questions'].label='Approved questions'
        self.fields['opens_at'].label='Opens at (Bangladesh time)'
        self.fields['closes_at'].label='Closes at (Bangladesh time)'
    def clean(self):
        data=super().clean()
        if data.get('opens_at') and data.get('closes_at') and data['closes_at']<=data['opens_at']:raise ValidationError('Closing time must be after opening time.')
        if data.get('questions') and data['questions'].count()>50:raise ValidationError('Use at most 50 questions.')
        if data.get('certificate_enabled') and data.get('kind')!='exam':raise ValidationError('Certificates are available for exams only.')
        if data.get('certificate_enabled') and any(ord(c)>126 or ord(c)<32 for c in data.get('title','')):raise ValidationError('Use an English assessment title for PDF certificates.')
        return data

class QuestionForm(forms.ModelForm):
    class Meta:model=Question;fields=['concept','question_text','option_a','option_b','option_c','option_d','correct_answer','difficulty','explanation']
    def __init__(self,*args,subject_ids,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['concept'].queryset=self.fields['concept'].queryset.filter(subject_id__in=subject_ids)

class ImportForm(forms.Form):
    subject=forms.ModelChoiceField(queryset=Subject.objects.none())
    file=forms.FileField(help_text='UTF-8 CSV, at most 1 MB / 500 questions. Rows enter pending review.')
    def __init__(self,*args,subject_ids,**kwargs):
        super().__init__(*args,**kwargs);self.fields['subject'].queryset=Subject.objects.filter(pk__in=subject_ids)
