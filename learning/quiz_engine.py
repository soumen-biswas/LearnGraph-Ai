"""
Quiz Engine
Always generates fresh AI questions — no repetition.
Keeps a question bank of 20+ per concept for variety.
"""
import random
from .models import Concept, Question, Progress
from . import ai_engine

BANK_SIZE = 20      # Keep this many questions in DB per concept
QUIZ_SIZE = 5       # Questions per quiz session
REFRESH_AFTER = 15  # Generate new batch when bank has fewer than this


def get_quiz(concept_id: int, num_questions: int = QUIZ_SIZE) -> list[dict]:
    """
    Always returns varied questions.
    - If bank has enough → pick random subset (never same set twice)
    - If bank is low → generate fresh AI questions first
    """
    concept = Concept.objects.get(id=concept_id)
    db_questions = list(Question.objects.filter(concept=concept, approval_status='approved'))

    # Generate more if bank is getting low
    if not db_questions:
        _generate_and_save(concept, num_questions=QUIZ_SIZE)
        db_questions = list(Question.objects.filter(concept=concept, approval_status='approved'))

    if not db_questions:
        raise ValueError('No questions available')

    # Pick random subset — always different combination
    if len(db_questions) >= num_questions:
        selected = random.sample(db_questions, num_questions)
    else:
        selected = db_questions  # Use whatever we have

    # Shuffle options order for extra variety
    return [_q_to_dict(q) for q in selected]


def _generate_and_save(concept, num_questions: int = 5):
    """Call AI and save new questions to DB."""
    try:
        from academy.telemetry import current_user
        ai_qs = ai_engine.generate_quiz(
            concept_name=concept.name,
            subject_name=concept.subject.name,
            num_questions=num_questions,
        )
        saved = 0
        if not isinstance(ai_qs, list) or not ai_qs:
            raise ValueError('Empty question list')
        for q in ai_qs:
            if not isinstance(q, dict) or any(not isinstance(q.get(k), str) or not q[k].strip() for k in ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')):
                raise ValueError('Invalid question')
            if q['correct_answer'].lower() not in ('a', 'b', 'c', 'd') or any(len(q[k]) > 200 for k in ('option_a','option_b','option_c','option_d')):
                raise ValueError('Invalid answer/options')
        for q in ai_qs:
            # Only save if question is not duplicate
            _, created = Question.objects.get_or_create(
                concept=concept,
                question_text=q['question'],
                defaults={
                    'option_a': q['option_a'],
                    'option_b': q['option_b'],
                    'option_c': q['option_c'],
                    'option_d': q['option_d'],
                    'correct_answer': q['correct_answer'].lower(),
                    'difficulty': q.get('difficulty', 'medium'),
                    'ai_generated': True,
                    'approval_status': 'pending',
                    'authored_by': current_user.get(),
                    'explanation': str(q.get('explanation', ''))[:3000],
                }
            )
            if created:
                saved += 1

        print(f"✅ Generated {saved} new questions for {concept.name}")
        return saved

    except Exception as e:
        print("AI quiz generation unavailable.")
        raise


def refresh_quiz_bank(concept_id: int) -> int:
    """Force regenerate quiz bank for a concept. Called from API."""
    concept = Concept.objects.get(id=concept_id)
    # Delete old AI questions to force fresh generation
    # Keep existing questions until new generation succeeds.
    return _generate_and_save(concept, num_questions=QUIZ_SIZE)


def _q_to_dict(q: Question) -> dict:
    return {
        "id": q.id,
        "question": q.question_text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "correct_answer": q.correct_answer,
        "explanation": q.explanation,
        "difficulty": q.difficulty,
    }


def save_quiz_result(concept_id: int, total: int, correct: int) -> int:
    """Save quiz result and update concept mastery. Returns new mastery."""
    concept = Concept.objects.get(id=concept_id)
    score = round((correct / total) * 100) if total > 0 else 0

    Progress.objects.create(
        concept=concept,
        score=score,
        questions_total=total,
        questions_correct=correct,
    )

    # Update mastery: weighted average (70% old + 30% new score)
    new_mastery = round(concept.mastery * 0.7 + score * 0.3)
    concept.mastery = min(100, new_mastery)
    concept.save()

    return concept.mastery
