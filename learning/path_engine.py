from .personalization import personal_concepts
"""
Learning Path Engine
Builds topologically-sorted learning paths based on dependencies and mastery.
"""
from .models import Subject, Concept, Dependency
from . import ai_engine


def get_learning_path(subject_id: int, user, use_ai: bool = True) -> dict:
    """
    Generate personalized learning path.
    First tries AI, falls back to algorithmic approach.
    """
    subject = Subject.objects.get(id=subject_id)
    concepts = personal_concepts(subject_id, user)

    weak = [{"name": c.name, "mastery": c.mastery} for c in concepts if c.mastery < 50]
    strong = [{"name": c.name, "mastery": c.mastery} for c in concepts if c.mastery >= 70]

    if use_ai and weak:
        try:
            result = ai_engine.generate_learning_path(subject.name, weak, strong)
            if not isinstance(result, dict) or not isinstance(result.get('path'), list):
                raise ValueError('Invalid learning path')
            result['source'] = 'ai'
            return result
        except Exception:
            pass

    # Fallback: algorithmic topological sort
    return _algorithmic_path(subject, concepts)


def _algorithmic_path(subject, concepts):
    """Topological sort + mastery-based priority."""
    deps = Dependency.objects.filter(concept__subject=subject).select_related('concept', 'prerequisite')

    concept_map = {c.id: c for c in concepts}
    prereq_map = {}
    for d in deps:
        prereq_map.setdefault(d.concept_id, []).append(d.prerequisite_id)

    def all_prereqs_ok(concept_id):
        prereqs = prereq_map.get(concept_id, [])
        return all(concept_map[pid].mastery >= 60 for pid in prereqs if pid in concept_map)

    # Sort: critical concepts first, prereqs satisfied, then by mastery asc
    prioritized = sorted(
        [c for c in concepts if c.mastery < 80],
        key=lambda c: (not all_prereqs_ok(c.id), c.mastery)
    )

    path = []
    for i, concept in enumerate(prioritized[:6], 1):
        path.append({
            "step": i,
            "concept": concept.name,
            "action": f"Study {concept.name}, implement examples, solve practice problems",
            "time": "3-4 hours",
            "priority": "High" if concept.mastery < 30 else "Medium",
            "resource": "GeeksForGeeks + LeetCode",
            "tip": "Practice explaining it to someone else",
        })

    return {
        "summary": f"Focus on your {len(weak := [c for c in concepts if c.mastery < 50])} weak areas in {subject.name}. Build from fundamentals.",
        "estimated_days": len(path) * 2,
        "path": path,
    }
