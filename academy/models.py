import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Batch(models.Model):
    completion_enabled=models.BooleanField(default=False)
    name=models.CharField(max_length=120)
    teacher=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='teaching_batches')
    subject=models.ForeignKey('learning.Subject',on_delete=models.PROTECT)
    students=models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True,related_name='enrolled_batches')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.name

class Assessment(models.Model):
    batch=models.ForeignKey(Batch,on_delete=models.PROTECT)
    title=models.CharField(max_length=160)
    kind=models.CharField(max_length=16,choices=[('exam','Exam'),('assignment','Assignment')],default='exam')
    instructions=models.TextField(blank=True)
    questions=models.ManyToManyField('learning.Question')
    opens_at=models.DateTimeField()
    closes_at=models.DateTimeField()
    duration_minutes=models.PositiveIntegerField(default=30,validators=[MinValueValidator(1),MaxValueValidator(1440)])
    max_attempts=models.PositiveIntegerField(default=1,validators=[MinValueValidator(1),MaxValueValidator(10)])
    pass_percent=models.PositiveIntegerField(default=80,validators=[MinValueValidator(1),MaxValueValidator(100)])
    published=models.BooleanField(default=False)
    results_released=models.BooleanField(default=False)
    certificate_enabled=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.title

class AssessmentAttempt(models.Model):
    assessment=models.ForeignKey(Assessment,on_delete=models.PROTECT)
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    number=models.PositiveIntegerField()
    questions=models.JSONField(default=list)
    answers=models.JSONField(default=list)
    pass_percent=models.PositiveIntegerField()
    started_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField()
    submitted_at=models.DateTimeField(null=True)
    score=models.PositiveIntegerField(null=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['assessment','student','number'],name='unique_assessment_attempt')]

class Certificate(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    attempt=models.OneToOneField(AssessmentAttempt,on_delete=models.CASCADE)
    recipient_name=models.CharField(max_length=180)
    course_title=models.CharField(max_length=160)
    issued_at=models.DateTimeField(auto_now_add=True)
    revoked_at=models.DateTimeField(null=True,blank=True)
    revoke_reason=models.CharField(max_length=200,blank=True)

class AuditEvent(models.Model):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=80)
    target=models.CharField(max_length=180)
    batch=models.ForeignKey(Batch,null=True,blank=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class AIUsage(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    operation=models.CharField(max_length=80)
    model=models.CharField(max_length=120)
    success=models.BooleanField(default=False)
    error_type=models.CharField(max_length=80,blank=True)
    prompt_tokens=models.PositiveIntegerField(default=0)
    completion_tokens=models.PositiveIntegerField(default=0)
    duration_ms=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class CourseCertificate(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    batch=models.ForeignKey(Batch,on_delete=models.PROTECT)
    recipient_name=models.CharField(max_length=100)
    course_title=models.CharField(max_length=160)
    quiz_score=models.DecimalField(max_digits=5,decimal_places=2)
    assignment_score=models.DecimalField(max_digits=5,decimal_places=2)
    score=models.DecimalField(max_digits=5,decimal_places=2)
    evidence=models.JSONField(default=dict)
    issued_at=models.DateTimeField(auto_now_add=True)
    revoked_at=models.DateTimeField(null=True,blank=True)
    revoke_reason=models.CharField(max_length=200,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['student','batch'],name='one_course_certificate_per_student_batch')]


class ProjectAssignment(models.Model):
    batch=models.ForeignKey(Batch,on_delete=models.PROTECT,related_name='projects')
    title=models.CharField(max_length=160)
    brief=models.TextField()
    rubric=models.TextField(help_text='Explain the criteria and marks, totaling 100.')
    opens_at=models.DateTimeField()
    closes_at=models.DateTimeField()
    published=models.BooleanField(default=False)
    results_released=models.BooleanField(default=False)
    ai_generated=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.title


class ProjectSubmission(models.Model):
    project=models.ForeignKey(ProjectAssignment,on_delete=models.PROTECT,related_name='submissions')
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    response=models.TextField(blank=True)
    work_url=models.URLField(max_length=500,blank=True)
    submitted_at=models.DateTimeField(null=True,blank=True)
    score=models.PositiveIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(100)])
    feedback=models.TextField(blank=True)
    reviewed_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='reviewed_projects')
    reviewed_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['project','student'],name='one_project_submission_per_student')]
