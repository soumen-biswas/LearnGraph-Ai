import csv,io
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from learning.models import Question,Concept
from .models import AssessmentAttempt

CSV_FIELDS=['concept','question','option_a','option_b','option_c','option_d','correct_answer','difficulty','explanation']

def parse_questions(upload,subject):
    if upload.size>1024*1024:raise ValidationError('CSV must be no larger than 1 MB.')
    try:
        text=upload.read().decode('utf-8-sig')
        reader=csv.DictReader(io.StringIO(text))
        if reader.fieldnames!=CSV_FIELDS:raise ValidationError('Use the exact columns from the CSV template in the same order.')
        concepts={c.name:c for c in Concept.objects.filter(subject=subject)}
        rows=[]
        for index,row in enumerate(reader,2):
            if len(rows)>=500:raise ValidationError('Limit each import to 500 rows.')
            if None in row or any(value is None for value in row.values()):raise ValidationError(f'Row {index}: invalid column count.')
            row={key:value.strip() for key,value in row.items()}
            if row['concept'] not in concepts:raise ValidationError(f'Row {index}: concept does not exist in the selected subject.')
            if not row['question'] or len(row['question'])>3000:raise ValidationError(f'Row {index}: question must contain 1–3000 characters.')
            if any(not row[k] or len(row[k])>200 for k in ['option_a','option_b','option_c','option_d']):raise ValidationError(f'Row {index}: each option needs 1–200 characters.')
            if row['correct_answer'] not in 'abcd' or len(row['correct_answer'])!=1:raise ValidationError(f'Row {index}: correct_answer must be a, b, c or d.')
            if row['difficulty'] not in ['easy','medium','hard']:raise ValidationError(f'Row {index}: invalid difficulty.')
            if len(row['explanation'])>3000:raise ValidationError(f'Row {index}: explanation is too long.')
            rows.append(Question(concept=concepts[row['concept']],question_text=row['question'],approval_status='pending',**{k:row[k] for k in CSV_FIELDS[2:]}))
        if not rows:raise ValidationError('The CSV is empty.')
        return rows
    except (UnicodeDecodeError,csv.Error) as exc:raise ValidationError('Provide a valid UTF-8 CSV file.') from exc


def finish_attempt(attempt,answers=None):
    """Caller locks the attempt inside a transaction. Deadline always comes from the server."""
    if attempt.submitted_at:return attempt
    if answers is not None:
        if not isinstance(answers,list) or len(answers)!=len(attempt.questions) or any(a not in ('','a','b','c','d') for a in answers):raise ValidationError('Invalid answer data.')
        attempt.answers=answers
    current=attempt.answers or ['']*len(attempt.questions)
    correct=sum(a==q['correct_answer'] for a,q in zip(current,attempt.questions))
    attempt.score=round(100*correct/len(attempt.questions)) if attempt.questions else 0
    attempt.submitted_at=timezone.now()
    attempt.save(update_fields=['answers','score','submitted_at'])
    return attempt


def csv_cell(value):
    value=str(value if value is not None else '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value
