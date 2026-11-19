from .personalization import personal_concepts
"""
Graph Engine — builds concept dependency graph data for Cytoscape.js / vis.js
"""
from .models import Subject, Concept, Dependency


def get_graph_data(subject_id: int, user) -> dict:
    """
    Returns nodes + edges in Cytoscape.js format.
    Color-codes nodes by mastery level.
    """
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        return {"nodes": [], "edges": []}

    concepts = personal_concepts(subject_id, user)
    deps = Dependency.objects.filter(concept__subject=subject).select_related('concept', 'prerequisite')

    nodes = []
    for c in concepts:
        nodes.append({
            "data": {
                "id": str(c.id),
                "label": c.name,
                "mastery": c.mastery,
                "level": c.mastery_level(),
                "color": c.mastery_color(),
                "description": c.description,
            },
            "position": {"x": c.pos_x or 100, "y": c.pos_y or 100},
        })

    edges = []
    for d in deps:
        edges.append({
            "data": {
                "id": f"e{d.id}",
                "source": str(d.prerequisite.id),
                "target": str(d.concept.id),
            }
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "subject": {"id": subject.id, "name": subject.name, "color": subject.color},
    }


def get_missing_prerequisites(subject_id: int) -> list:
    """
    Returns concepts where prerequisites are weak (< 50%)
    but the concept itself has been attempted (mastery > 0).
    """
    gaps = []
    deps = Dependency.objects.filter(
        concept__subject_id=subject_id
    ).select_related('concept', 'prerequisite')

    for d in deps:
        if d.prerequisite.mastery < 50 and d.concept.mastery > 0:
            gaps.append({
                "concept": d.concept.name,
                "missing_prereq": d.prerequisite.name,
                "prereq_mastery": d.prerequisite.mastery,
                "concept_mastery": d.concept.mastery,
            })
    return gaps


def update_concept_position(concept_id: int, x: int, y: int):
    """Save node position after user drags it."""
    Concept.objects.filter(id=concept_id).update(pos_x=int(x), pos_y=int(y))
