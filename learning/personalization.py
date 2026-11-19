from .models import Concept, UserProgress

def personal_concepts(subject_id, user):
    concepts = list(Concept.objects.filter(subject_id=subject_id))
    scores = dict(UserProgress.objects.filter(user=user, concept__subject_id=subject_id).values_list('concept_id', 'mastery'))
    for concept in concepts:
        concept.mastery = scores.get(concept.pk, 0)
    return concepts

def mastery_for(user, concept):
    return UserProgress.objects.filter(user=user, concept=concept).values_list('mastery', flat=True).first() or 0
