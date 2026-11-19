from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📚')
    color = models.CharField(max_length=20, default='#3b82f6')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Concept(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mastery = models.IntegerField(default=0)  # 0-100
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subject', 'name')

    def __str__(self):
        return f"{self.subject.name} → {self.name}"

    def mastery_level(self):
        if self.mastery >= 80: return 'Mastered'
        if self.mastery >= 50: return 'Learning'
        if self.mastery >= 25: return 'Weak'
        return 'Critical'

    def mastery_color(self):
        if self.mastery >= 80: return '#10b981'
        if self.mastery >= 50: return '#3b82f6'
        if self.mastery >= 25: return '#f59e0b'
        return '#ef4444'


class Dependency(models.Model):
    """prerequisite → concept"""
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='prerequisites')
    prerequisite = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='leads_to')

    class Meta:
        unique_together = ('concept', 'prerequisite')

    def __str__(self):
        return f"{self.prerequisite.name} → {self.concept.name}"


class Question(models.Model):
    approval_status = models.CharField(max_length=12, choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')], default='approved')
    authored_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='authored_questions')
    reviewed_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_questions')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    DIFFICULTY = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('a','A'),('b','B'),('c','C'),('d','D')])
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.concept.name}] {self.question_text[:60]}"


class Progress(models.Model):
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='progress_records')
    score = models.IntegerField()          # quiz score %
    questions_total = models.IntegerField(default=0)
    questions_correct = models.IntegerField(default=0)
    session_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.concept.name} — {self.score}% on {self.session_date.date()}"


# ── AUTH MODELS ───────────────────────────────────────────────────────────────
import secrets
import string
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {'verified' if self.is_email_verified else 'unverified'}"


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="verifications")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.conf import settings
        expiry_minutes = getattr(settings, "VERIFICATION_CODE_EXPIRY", 10)
        return (
            not self.is_used and
            timezone.now() < self.created_at + timedelta(minutes=expiry_minutes)
        )

    @staticmethod
    def generate_code():
        return "".join((secrets.choice(string.digits) for _ in range(6)))

    def __str__(self):
        return f"{self.user.username} — verification ({'used' if self.is_used else 'active'})"


class UserProgress(models.Model):
    review_due = models.DateField(null=True, blank=True)
    review_interval = models.PositiveIntegerField(default=1)
    """Link user to their concept progress."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_progress")
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name="user_progress")
    mastery = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "concept")

    def __str__(self):
        return f"{self.user.username} — {self.concept.name}: {self.mastery}%"


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    questions = models.JSONField(default=list)  # Server-only answer snapshots
    answers = models.JSONField(default=list)
    score = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True)


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='New conversation')
    messages = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)


class StudyGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CourseNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    content = models.TextField()
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
