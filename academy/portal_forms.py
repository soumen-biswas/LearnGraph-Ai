from django import forms
from django.contrib.auth.models import User
from learning.models import Subject, Concept, Dependency
from .models import Batch


class AccountForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('student', 'Student'), ('teacher', 'Teacher')])
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not email or User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Enter a unique account email.')
        return email


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']


class ConceptForm(forms.ModelForm):
    prerequisites = forms.ModelMultipleChoiceField(queryset=Concept.objects.none(), required=False)
    class Meta:
        model = Concept
        fields = ['name', 'description']
    def __init__(self, *args, subject, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = subject
        self.fields['prerequisites'].queryset = Concept.objects.filter(subject=subject).exclude(pk=self.instance.pk)
        if self.instance.pk:
            self.fields['prerequisites'].initial = self.instance.prerequisites.values_list('prerequisite_id', flat=True)
    def clean(self):
        data = super().clean()
        if Concept.objects.filter(subject=self.subject, name=data.get('name')).exclude(pk=self.instance.pk).exists():
            self.add_error('name', 'This concept already exists.')
        # Follow prerequisite chains; reject any new cycle.
        for prerequisite in data.get('prerequisites', []):
            todo, seen = [prerequisite.pk], set()
            while todo:
                node = todo.pop()
                if node == self.instance.pk:
                    raise forms.ValidationError('These prerequisites would create a cycle.')
                if node not in seen:
                    seen.add(node)
                    todo.extend(Dependency.objects.filter(concept_id=node).values_list('prerequisite_id', flat=True))
        return data


class AssignmentGeneratorForm(forms.Form):
    title = forms.CharField(max_length=160)
    concepts = forms.ModelMultipleChoiceField(queryset=Concept.objects.none(), help_text='Choose up to three concepts.')
    difficulty = forms.ChoiceField(choices=[('easy','Easy'),('medium','Medium'),('hard','Hard')])
    opens_at = forms.DateTimeField(label='Opens at (Bangladesh time)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type':'datetime-local'}))
    closes_at = forms.DateTimeField(label='Closes at (Bangladesh time)', widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type':'datetime-local'}))
    def __init__(self, *args, batch, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['concepts'].queryset = Concept.objects.filter(subject=batch.subject)
    def clean(self):
        data = super().clean()
        if len(data.get('concepts', [])) > 3:
            self.add_error('concepts', 'Choose up to three concepts.')
        if data.get('opens_at') and data.get('closes_at') and data['closes_at'] <= data['opens_at']:
            self.add_error('closes_at', 'Closing time must be after opening time.')
        return data
