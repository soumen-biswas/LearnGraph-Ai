from decimal import Decimal, ROUND_HALF_UP
from learning.models import QuizAttempt
from .models import Assessment, AssessmentAttempt, ProjectAssignment, ProjectSubmission


def eligibility(student, batch):
    """Latest submitted evidence, not client scores. No unreleased marks exposed."""
    concepts = list(batch.subject.concepts.order_by('pk'))
    assignments = list(Assessment.objects.filter(batch=batch, kind='assignment', published=True).order_by('pk'))
    projects=list(ProjectAssignment.objects.filter(batch=batch,published=True).order_by('pk'))
    project_ids=[]
    quiz_ids, assignment_ids, quiz_marks, assignment_marks, missing = [], [], [], [], []
    if not batch.completion_enabled:
        missing.append('Your teacher has not enabled course certificates for this class.')
    if not concepts:
        missing.append('No course concepts have been defined.')
    if not assignments and not projects:
        missing.append('At least one published assignment is required.')
    for concept in concepts:
        attempt = QuizAttempt.objects.filter(user=student, concept=concept, submitted_at__isnull=False,
            score__isnull=False, created_at__gte=batch.created_at).order_by('-submitted_at','-pk').first()
        if attempt:
            quiz_ids.append(attempt.pk); quiz_marks.append(Decimal(attempt.score))
        else:
            missing.append('Complete a practice quiz: ' + concept.name)
    for assessment in assignments:
        if not assessment.results_released:
            missing.append('Awaiting released results: ' + assessment.title)
            continue
        attempt = AssessmentAttempt.objects.filter(student=student, assessment=assessment,
            submitted_at__isnull=False, score__isnull=False).order_by('-submitted_at','-pk').first()
        if attempt:
            assignment_ids.append(attempt.pk); assignment_marks.append(Decimal(attempt.score))
        else:
            missing.append('Complete assignment: ' + assessment.title)
    for project in projects:
        if not project.results_released:
            missing.append('Awaiting released project results: '+project.title)
            continue
        submission=ProjectSubmission.objects.filter(project=project,student=student,submitted_at__isnull=False,score__isnull=False,reviewed_at__isnull=False).first()
        if submission:
            project_ids.append(submission.pk);assignment_marks.append(Decimal(submission.score))
        else:missing.append('Complete project and await teacher grading: '+project.title)
    quiz = sum(quiz_marks, Decimal(0)) / len(quiz_marks) if quiz_marks else Decimal(0)
    assignment = sum(assignment_marks, Decimal(0)) / len(assignment_marks) if assignment_marks else Decimal(0)
    total = quiz * Decimal('.4') + assignment * Decimal('.6')
    if not missing and (total < 70 or quiz < 50 or assignment < 50):
        missing.append('Reach 70% overall and at least 50% in each component.')
    return {'eligible': not missing, 'missing': missing,
        'quiz_score': quiz.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
        'assignment_score': assignment.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
        'score': total.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
        'quiz_done':len(quiz_marks), 'quiz_total':len(concepts),
        'assignment_done':len(assignment_marks), 'assignment_total':len(assignments)+len(projects),
        'evidence': {'quiz_attempts':quiz_ids, 'assignment_attempts':assignment_ids,
            'policy':'v2: latest quiz/MCQ attempts and final teacher-graded projects; quiz 40%; assignment 60%; pass 70%; component minimum 50%; assignments/projects equally weighted',
            'project_submissions':project_ids,'project_ids':[p.pk for p in projects],
            'concept_ids':[c.pk for c in concepts], 'assessment_ids':[a.pk for a in assignments]}}
