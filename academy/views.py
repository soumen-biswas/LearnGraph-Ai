import csv,io,json
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.db.models import Avg,Sum,Count,Q
from django.http import HttpResponse,JsonResponse,FileResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from learning.models import Subject,Question,UserProgress,Concept
from learning.quiz_engine import _q_to_dict
from .models import Batch,Assessment,AssessmentAttempt,Certificate,AuditEvent,AIUsage,ProjectAssignment
from .access import teacher_required,batches_for,is_teacher,audit
from .forms import BatchForm,EnrollmentForm,AssessmentForm,QuestionForm,ImportForm
from .services import parse_questions,CSV_FIELDS,finish_attempt,csv_cell


def teacher_context(user):
    batches=batches_for(user)
    return {'teacher_mode':True,'managed_batches':batches}

@teacher_required
def dashboard(request):
    batches=batches_for(request.user).select_related('subject','teacher').annotate(student_count=Count('students',distinct=True))
    subjects=batches.values_list('subject_id',flat=True)
    attempts=AssessmentAttempt.objects.filter(assessment__batch__in=batches,submitted_at__isnull=False)
    context=teacher_context(request.user)
    context.update(batches=batches,pending_count=Question.objects.filter(concept__subject_id__in=subjects,approval_status='pending').count(),student_count=User.objects.filter(enrolled_batches__in=batches).distinct().count(),attempt_count=attempts.count(),average=round(attempts.aggregate(value=Avg('score'))['value'] or 0),recent=attempts.select_related('student','assessment').order_by('-submitted_at')[:8])
    return render(request,'academy/dashboard.html',context)

@teacher_required
def batch_create(request):
    form=BatchForm(request.POST or None,user=request.user)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            batch=form.save(commit=False);batch.teacher=form.cleaned_data.get('teacher') or request.user;batch.save();audit(request.user,'batch.created',batch.pk,batch)
        return redirect('academy_batch',pk=batch.pk)
    return render(request,'academy/form.html',{'form':form,'title':'Create a class','description':'Choose its subject. Students can then be enrolled by their account email.'})

@teacher_required
def batch_detail(request,pk):
    batch=get_object_or_404(batches_for(request.user),pk=pk)
    form=EnrollmentForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        student=User.objects.filter(email__iexact=form.cleaned_data['email'],is_active=True,is_staff=False).first()
        if student is None:form.add_error('email','No active student account matches this address.')
        else:
            with transaction.atomic():batch.students.add(student);audit(request.user,'student.enrolled',student.pk,batch)
            messages.success(request,'Student enrolled.');return redirect('academy_batch',pk=batch.pk)
    students=batch.students.annotate(avg_mastery=Avg('user_progress__mastery',filter=Q(user_progress__concept__subject=batch.subject)))
    return render(request,'academy/batch.html',{'batch':batch,'form':form,'students_list':students,'assessments':Assessment.objects.filter(batch=batch).order_by('-created_at')})

@teacher_required
@require_POST
def unenroll(request,pk,student_id):
    batch=get_object_or_404(batches_for(request.user),pk=pk)
    with transaction.atomic():batch.students.remove(student_id);audit(request.user,'student.unenrolled',student_id,batch)
    return redirect('academy_batch',pk=pk)

@teacher_required
def student_detail(request,pk,student_id):
    batch=get_object_or_404(batches_for(request.user),pk=pk)
    student=get_object_or_404(batch.students,pk=student_id)
    progress=UserProgress.objects.filter(user=student,concept__subject=batch.subject).select_related('concept')
    attempts=AssessmentAttempt.objects.filter(student=student,assessment__batch=batch).select_related('assessment').order_by('-started_at')
    return render(request,'academy/student.html',{'student':student,'batch':batch,'progress':progress,'attempts':attempts})

@teacher_required
def question_queue(request):
    subjects=(Subject.objects.values_list('pk',flat=True) if request.user.is_superuser else batches_for(request.user).values_list('subject_id',flat=True))
    status=request.GET.get('status','pending')
    if status not in ('pending','approved','rejected'):status='pending'
    questions=Question.objects.filter(concept__subject_id__in=subjects,approval_status=status).select_related('concept','authored_by').order_by('-created_at')[:100]
    return render(request,'academy/questions.html',{'questions':questions,'status':status,'concepts':Concept.objects.filter(subject_id__in=subjects).select_related('subject')})

@teacher_required
def question_create(request):
    form=QuestionForm(request.POST or None,subject_ids=(Subject.objects.values_list('pk',flat=True) if request.user.is_superuser else batches_for(request.user).values_list('subject_id',flat=True)))
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            question=form.save(commit=False);question.authored_by=request.user;question.approval_status='pending';question.save();audit(request.user,'question.created',question.pk)
        return redirect('academy_questions')
    return render(request,'academy/form.html',{'form':form,'title':'Draft a question','description':'New questions enter review before students can use them.'})

@teacher_required
@require_POST
def review_question(request,pk):
    question=get_object_or_404(Question,pk=pk,concept__subject_id__in=(Subject.objects.values_list('pk',flat=True) if request.user.is_superuser else batches_for(request.user).values_list('subject_id',flat=True)))
    decision=request.POST.get('decision')
    if decision not in ('approved','rejected'):raise PermissionDenied
    with transaction.atomic():
        question.approval_status=decision;question.reviewed_by=request.user;question.reviewed_at=timezone.now();question.save(update_fields=['approval_status','reviewed_by','reviewed_at']);audit(request.user,'question.'+decision,question.pk)
    return redirect('academy_questions')

@teacher_required
def import_questions(request):
    form=ImportForm(request.POST or None,request.FILES or None,subject_ids=(Subject.objects.values_list('pk',flat=True) if request.user.is_superuser else batches_for(request.user).values_list('subject_id',flat=True)))
    if request.method=='POST' and form.is_valid():
        try:
            rows=parse_questions(form.cleaned_data['file'],form.cleaned_data['subject'])
            with transaction.atomic():
                for row in rows:row.authored_by=request.user
                Question.objects.bulk_create(rows);audit(request.user,'questions.imported',f'{len(rows)} questions')
            messages.success(request,f'{len(rows)} questions imported for review.');return redirect('academy_questions')
        except ValidationError as exc:form.add_error('file',exc)
    return render(request,'academy/form.html',{'form':form,'title':'Import question bank','description':'Download the CSV template first. All rows are validated before any are saved.','import_mode':True})

@teacher_required
def csv_template(request):
    response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="question-template.csv"'
    writer=csv.writer(response);writer.writerow(CSV_FIELDS);writer.writerow(['Stack','Which ordering rule does a stack follow?','LIFO','FIFO','Sorted','Random','a','easy','The most recently pushed item is removed first.']);return response

@teacher_required
def assessment_create(request,pk):
    batch=get_object_or_404(batches_for(request.user),pk=pk)
    form=AssessmentForm(request.POST or None,batch=batch)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            assessment=form.save(commit=False);assessment.batch=batch;assessment.save();form.save_m2m();audit(request.user,'assessment.created',assessment.pk,batch)
        messages.success(request,'Draft created. Publish it from the class page when ready.');return redirect('academy_batch',pk=pk)
    return render(request,'academy/form.html',{'form':form,'title':'Create an assessment','description':f'{batch.name} · Enter Bangladesh time (BDT, UTC+6). An assignment is an untimed-until-deadline MCQ activity; exams also enforce the duration.'})

@teacher_required
@require_POST
def assessment_action(request,pk):
    assessment=get_object_or_404(Assessment,pk=pk,batch__in=batches_for(request.user))
    action=request.POST.get('action')
    with transaction.atomic():
        if action=='publish':
            if not assessment.questions.exists() or assessment.questions.exclude(approval_status='approved').exists():
                messages.error(request,'Publish requires approved questions only.');return redirect('academy_batch',pk=assessment.batch_id)
            assessment.published=True
        elif action=='unpublish':assessment.published=False
        elif action=='release':
            if timezone.now()<assessment.closes_at:
                messages.error(request,'Release results after the assessment closes.');return redirect('academy_batch',pk=assessment.batch_id)
            for pending in AssessmentAttempt.objects.select_for_update().filter(assessment=assessment,submitted_at__isnull=True):
                finish_attempt(pending)
            assessment.results_released=True
        else:raise PermissionDenied
        assessment.save();audit(request.user,'assessment.'+action,assessment.pk,assessment.batch)
    return redirect('academy_batch',pk=assessment.batch_id)

@login_required
def student_assessments(request):
    assessments=Assessment.objects.filter(batch__students=request.user,published=True).select_related('batch').distinct().order_by('closes_at')
    attempts=AssessmentAttempt.objects.filter(student=request.user).select_related('assessment').order_by('-started_at')
    certificates=Certificate.objects.filter(attempt__student=request.user).select_related('attempt__assessment')
    return render(request,'academy/assessments.html',{'assessments':assessments,'attempts':attempts,'certificates':certificates,'project_assignments':ProjectAssignment.objects.filter(batch__students=request.user,published=True).select_related('batch').distinct().order_by('closes_at')})

@login_required
@require_POST
def start_assessment(request,pk):
    with transaction.atomic():
        # Lock the parent row as well, serializing first-attempt creation on PostgreSQL.
        assessment=get_object_or_404(Assessment.objects.select_for_update(),pk=pk,published=True,batch__students=request.user)
        now=timezone.now()
        if not assessment.opens_at<=now<assessment.closes_at:
            messages.error(request,'This assessment is not open.');return redirect('academy_assessments')
        previous=AssessmentAttempt.objects.filter(assessment=assessment,student=request.user).order_by('-number').first()
        if previous and not previous.submitted_at:
            if previous.expires_at>now:return redirect('academy_take',pk=previous.pk)
            finish_attempt(previous)
        number=(previous.number if previous else 0)+1
        if number>assessment.max_attempts:
            messages.error(request,'You have used all attempts.');return redirect('academy_assessments')
        questions=list(assessment.questions.filter(approval_status='approved'))
        if not questions or len(questions)!=assessment.questions.count():
            messages.error(request,'This assessment needs teacher review before it can start.');return redirect('academy_assessments')
        expires=min(assessment.closes_at,now+timedelta(minutes=assessment.duration_minutes)) if assessment.kind=='exam' else assessment.closes_at
        attempt=AssessmentAttempt.objects.create(assessment=assessment,student=request.user,number=number,questions=[_q_to_dict(q) for q in questions],expires_at=expires,pass_percent=assessment.pass_percent)
        audit(request.user,'attempt.started',attempt.pk,assessment.batch)
    return redirect('academy_take',pk=attempt.pk)

@login_required
def take_assessment(request,pk):
    with transaction.atomic():
        attempt=get_object_or_404(AssessmentAttempt.objects.select_for_update().select_related('assessment__batch'),pk=pk,student=request.user)
        if attempt.submitted_at:return redirect('academy_result',pk=pk)
        if timezone.now()>=attempt.expires_at:finish_attempt(attempt);return redirect('academy_result',pk=pk)
    public=[]
    for index,q in enumerate(attempt.questions):
        public.append({'index':index,'question':q['question'],'options':[(l,q['option_'+l]) for l in 'abcd'],'answer':attempt.answers[index] if index<len(attempt.answers) else ''})
    return render(request,'academy/take.html',{'attempt':attempt,'questions':public})

@login_required
@require_POST
def save_assessment(request,pk):
    try:data=json.loads(request.body);answers=data.get('answers')
    except (ValueError,AttributeError):return JsonResponse({'error':'Invalid data.'},status=400)
    if not isinstance(answers,list) or any(a not in ('','a','b','c','d') for a in answers):return JsonResponse({'error':'Invalid answers.'},status=400)
    with transaction.atomic():
        attempt=get_object_or_404(AssessmentAttempt.objects.select_for_update(),pk=pk,student=request.user)
        if attempt.submitted_at:return JsonResponse({'error':'Already submitted.','finished':True},status=409)
        if timezone.now()>=attempt.expires_at:
            finish_attempt(attempt);return JsonResponse({'error':'Time expired. Last saved answers were graded.','finished':True},status=409)
        if len(answers)!=len(attempt.questions):return JsonResponse({'error':'Invalid answer count.'},status=400)
        attempt.answers=answers;attempt.save(update_fields=['answers'])
        if data.get('submit'):
            finish_attempt(attempt);audit(request.user,'attempt.submitted',attempt.pk,attempt.assessment.batch)
    return JsonResponse({'ok':True,'finished':bool(attempt.submitted_at)})

@login_required
def result(request,pk):
    attempt=get_object_or_404(AssessmentAttempt.objects.select_related('assessment'),pk=pk,student=request.user)
    if not attempt.submitted_at:return redirect('academy_take',pk=pk)
    review=[]
    if attempt.assessment.results_released:
        for q,a in zip(attempt.questions,attempt.answers or ['']*len(attempt.questions)):
            review.append({'question':q['question'],'answer':a or 'Unanswered','correct':q['option_'+q['correct_answer']],'explanation':q.get('explanation','')})
    return render(request,'academy/result.html',{'attempt':attempt,'review':review,'passed':attempt.score>=attempt.pass_percent,'certificate':Certificate.objects.filter(attempt=attempt).first()})

@login_required
@require_POST
def issue_certificate(request,pk):
    with transaction.atomic():
        attempt=get_object_or_404(AssessmentAttempt.objects.select_for_update().select_related('assessment'),pk=pk,student=request.user)
        if not attempt.submitted_at or attempt.score<attempt.pass_percent or not attempt.assessment.results_released or not attempt.assessment.certificate_enabled or attempt.assessment.kind!='exam':raise PermissionDenied
        name=request.POST.get('name','').strip()
        if not 2<=len(name)<=100 or not all(32<=ord(c)<127 for c in name) or request.POST.get('consent')!='yes':
            messages.error(request,'Use an English display name (2–100 characters) and consent to public certificate verification.');return redirect('academy_result',pk=pk)
        certificate,created=Certificate.objects.get_or_create(attempt=attempt,defaults={'recipient_name':name,'course_title':attempt.assessment.title})
        if created:audit(request.user,'certificate.issued',certificate.pk,attempt.assessment.batch)
    return redirect('academy_certificate',pk=certificate.pk)

@login_required
def certificate_pdf(request,pk):
    certificate=get_object_or_404(Certificate.objects.select_related('attempt__assessment__batch'),pk=pk)
    if certificate.attempt.student_id!=request.user.pk and not (is_teacher(request.user) and batches_for(request.user).filter(pk=certificate.attempt.assessment.batch_id).exists()):raise PermissionDenied
    if certificate.revoked_at:return HttpResponse('This certificate has been revoked.',status=410)
    from .pdf import render_certificate
    response=HttpResponse(render_certificate(certificate),content_type='application/pdf');response['Content-Disposition']=f'attachment; filename="certificate-{certificate.pk}.pdf"';response['Cache-Control']='private, no-store';return response


def verify_certificate(request,pk):
    certificate=get_object_or_404(Certificate,pk=pk)
    return render(request,'academy/verify.html',{'certificate':certificate})

@teacher_required
@require_POST
def revoke_certificate(request,pk):
    certificate=get_object_or_404(Certificate,pk=pk,attempt__assessment__batch__in=batches_for(request.user))
    with transaction.atomic():
        certificate.revoked_at=timezone.now();certificate.revoke_reason=request.POST.get('reason','Revoked by issuer')[:200];certificate.save();audit(request.user,'certificate.revoked',certificate.pk,certificate.attempt.assessment.batch)
    messages.success(request,'Certificate revoked. Its verification page now shows the revoked status.');return redirect('academy_reports')

@teacher_required
def reports(request):
    batches=batches_for(request.user)
    attempts=AssessmentAttempt.objects.filter(assessment__batch__in=batches,submitted_at__isnull=False).select_related('assessment__batch','student').order_by('-submitted_at')
    if request.GET.get('batch'):
        batch=get_object_or_404(batches,pk=request.GET['batch']);attempts=attempts.filter(assessment__batch=batch)
    if request.GET.get('download')=='csv':
        response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="assessment-report.csv"'
        writer=csv.writer(response);writer.writerow(['Class','Assessment','Student','Email','Attempt','Score','Submitted UTC'])
        for attempt in attempts.iterator():writer.writerow([csv_cell(v) for v in [attempt.assessment.batch.name,attempt.assessment.title,attempt.student.get_full_name(),attempt.student.email,attempt.number,attempt.score,attempt.submitted_at.isoformat()]])
        audit(request.user,'report.exported','assessment CSV');return response
    certificates=Certificate.objects.filter(attempt__assessment__batch__in=batches).select_related('attempt__assessment')[:100]
    return render(request,'academy/reports.html',{'batches':batches,'attempts':attempts[:200],'certificates':certificates})

@teacher_required
def usage(request):
    if not request.user.is_superuser:raise PermissionDenied
    rows=AIUsage.objects.all()
    stats=rows.aggregate(requests=Count('id'),input_tokens=Sum('prompt_tokens'),output_tokens=Sum('completion_tokens'))
    stats['failed']=rows.filter(success=False).count()
    return render(request,'academy/usage.html',{'stats':stats,'usage_rows':rows.select_related('user')[:100]})

@teacher_required
def audit_log(request):
    rows=AuditEvent.objects.all() if request.user.is_superuser else AuditEvent.objects.filter(Q(batch__in=batches_for(request.user))|Q(actor=request.user))
    return render(request,'academy/audit.html',{'events':rows.select_related('actor')[:200]})


@teacher_required
@require_POST
def generate_questions(request):
    concept=get_object_or_404(Concept,pk=request.POST.get('concept'),subject_id__in=(Subject.objects.values_list('pk',flat=True) if request.user.is_superuser else batches_for(request.user).values_list('subject_id',flat=True)))
    from learning.quiz_engine import refresh_quiz_bank
    from learning.ai_errors import explain_error
    try:
        saved=refresh_quiz_bank(concept.pk)
        audit(request.user,'questions.generated',f'concept {concept.pk}; {saved} draft(s)')
        messages.success(request,f'{saved} new draft questions await review.')
    except Exception as exc:messages.error(request,explain_error(exc))
    return redirect('academy_questions')


@teacher_required
def batch_edit(request,pk):
    batch=get_object_or_404(batches_for(request.user),pk=pk)
    form=BatchForm(request.POST or None,instance=batch,user=request.user)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():form.save();audit(request.user,'batch.updated',batch.pk,batch)
        return redirect('academy_dashboard')
    return render(request,'academy/form.html',{'form':form,'title':'Edit class','description':'The subject is fixed to preserve progress and assessment history. Administrators may reassign the teacher.'})

@teacher_required
def assessment_edit(request,pk):
    assessment=get_object_or_404(Assessment,pk=pk,batch__in=batches_for(request.user))
    if assessment.published or AssessmentAttempt.objects.filter(assessment=assessment).exists():
        messages.error(request,'Only an unpublished assessment with no attempts can be edited.')
        return redirect('academy_batch',pk=assessment.batch_id)
    form=AssessmentForm(request.POST or None,instance=assessment,batch=assessment.batch)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            locked=Assessment.objects.select_for_update().get(pk=assessment.pk)
            if locked.published or AssessmentAttempt.objects.filter(assessment=locked).exists():
                messages.error(request,'The assessment is no longer editable.');return redirect('academy_batch',pk=assessment.batch_id)
            form.save();audit(request.user,'assessment.updated',assessment.pk,assessment.batch)
        return redirect('academy_batch',pk=assessment.batch_id)
    return render(request,'academy/form.html',{'form':form,'title':'Edit draft assessment','description':'Enter Bangladesh time (BDT, UTC+6). Publish from the class page after reviewing the draft.'})
