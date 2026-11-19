from .personalization import personal_concepts
"""
Missing Concept Detection Engine
Identifies knowledge gaps based on prerequisite chains.
"""
from .models import Subject, Concept, Dependency


def detect_missing_concepts(subject_id: int, user) -> dict:
    """
    Full analysis of missing/weak prerequisites.
    Returns categorized gaps with recommendations.
    """
    subject = Subject.objects.get(id=subject_id)
    concepts = {c.id: c for c in personal_concepts(subject_id, user)}
    deps = Dependency.objects.filter(concept__subject=subject).select_related('concept', 'prerequisite')

    critical_gaps = []    # mastery < 25
    weak_gaps = []        # mastery 25-49
    ready_to_learn = []   # all prereqs >= 70, concept < 50

    for concept in concepts.values():
        prereqs = [concepts[d.prerequisite_id] for d in deps if d.concept_id == concept.id and d.prerequisite_id in concepts]

        if not prereqs:
            continue

        for p in prereqs:
            if p.mastery < 25:
                critical_gaps.append({
                    "concept": concept.name,
                    "blocked_by": p.name,
                    "prereq_mastery": p.mastery,
                })
            elif p.mastery < 50:
                weak_gaps.append({
                    "concept": concept.name,
                    "weak_prereq": p.name,
                    "prereq_mastery": p.mastery,
                })

        if all(p.mastery >= 70 for p in prereqs) and concept.mastery < 50:
            ready_to_learn.append({
                "concept": concept.name,
                "mastery": concept.mastery,
                "prereqs_ready": [p.name for p in prereqs],
            })

    # Overall weak concepts sorted by mastery
    weak_concepts = sorted(
        [{"name": c.name, "mastery": c.mastery, "level": c.mastery_level()}
         for c in concepts.values() if c.mastery < 50],
        key=lambda x: x["mastery"]
    )

    return {
        "subject": subject.name,
        "critical_gaps": critical_gaps,
        "weak_gaps": weak_gaps,
        "ready_to_learn": ready_to_learn,
        "weak_concepts": weak_concepts,
        "total_concepts": len(concepts),
        "mastered_count": sum(1 for c in concepts.values() if c.mastery >= 80),
        "avg_mastery": round(sum(c.mastery for c in concepts.values()) / len(concepts)) if concepts else 0,
    }
