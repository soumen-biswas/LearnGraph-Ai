from .personalization import personal_concepts
"""
Analytics Engine
Progress tracking, charts data, and AI-powered insights.
"""
from django.db.models import Avg, Count
from .models import Subject, Concept, Progress
from . import ai_engine


def get_dashboard_data(subject_id: int, user) -> dict:
    """Full dashboard data for a subject."""
    subject = Subject.objects.get(id=subject_id)
    concepts = personal_concepts(subject_id, user)

    total = len(concepts)
    mastered = [c for c in concepts if c.mastery >= 80]
    learning = [c for c in concepts if 50 <= c.mastery < 80]
    weak = [c for c in concepts if 25 <= c.mastery < 50]
    critical = [c for c in concepts if c.mastery < 25]
    avg_mastery = round(sum(c.mastery for c in concepts) / total) if total else 0

    # Bar chart data
    chart_labels = [c.name for c in sorted(concepts, key=lambda x: x.mastery, reverse=True)]
    chart_values = [c.mastery for c in sorted(concepts, key=lambda x: x.mastery, reverse=True)]
    chart_colors = [c.mastery_color() for c in sorted(concepts, key=lambda x: x.mastery, reverse=True)]

    # Recent quiz history (last 10)
    recent_progress = Progress.objects.filter(
        concept__subject=subject, user=user
    ).order_by('-session_date')[:10].values(
        'concept__name', 'score', 'session_date', 'questions_correct', 'questions_total'
    )

    # Achievements
    achievements = _compute_achievements(concepts, avg_mastery)
    achievements[0]["earned"] = Progress.objects.filter(user=user, concept__subject=subject).exists()

    return {
        "subject": {"id": subject.id, "name": subject.name},
        "stats": {
            "total": total,
            "avg_mastery": avg_mastery,
            "mastered": len(mastered),
            "learning": len(learning),
            "weak": len(weak),
            "critical": len(critical),
        },
        "chart": {
            "labels": chart_labels,
            "values": chart_values,
            "colors": chart_colors,
        },
        "concepts": [
            {"name": c.name, "mastery": c.mastery, "level": c.mastery_level(), "color": c.mastery_color()}
            for c in concepts
        ],
        "recent_progress": list(recent_progress),
        "achievements": achievements,
        "weakest": [
            {"name": c.name, "mastery": c.mastery}
            for c in sorted(concepts, key=lambda x: x.mastery)[:5]
        ],
    }


def get_ai_analytics(subject_id: int, user) -> dict:
    """Get AI-powered analytics insights."""
    subject = Subject.objects.get(id=subject_id)
    concepts = personal_concepts(subject_id, user)
    concepts_data = [{"name": c.name, "mastery": c.mastery} for c in concepts]

    try:
        return ai_engine.get_ai_recommendations(subject.name, concepts_data)
    except Exception as e:
        return {
            "recommendations": [
                "Focus on your weakest concepts daily",
                "Practice implementing algorithms from scratch",
                "Join a study group for peer learning",
            ],
            "predicted_score": max(30, min(95, sum(c.mastery for c in concepts) // len(concepts) + 5)) if concepts else 50,
            "bottlenecks": [c.name for c in sorted(concepts, key=lambda x: x.mastery)[:2]],
            "weekly_plan": [
                "Day 1: Review foundational concepts",
                "Day 2: Practice weak area 1",
                "Day 3: Practice weak area 2",
                "Day 4: Implement data structures",
                "Day 5: Solve 5 problems",
                "Day 6: Review and revise",
                "Day 7: Mock test",
            ],
            "error": "AI service unavailable",
        }


def _compute_achievements(concepts, avg_mastery):
    mastered_count = sum(1 for c in concepts if c.mastery >= 80)
    critical_count = sum(1 for c in concepts if c.mastery < 25)
    return [
        {"icon": "🌟", "label": "First Step", "desc": "Started your journey", "earned": True},
        {"icon": "🔥", "label": "On Fire", "desc": "50%+ avg mastery", "earned": avg_mastery >= 50},
        {"icon": "💡", "label": "Top Student", "desc": "80%+ avg mastery", "earned": avg_mastery >= 80},
        {"icon": "🎓", "label": "Expert", "desc": "5+ concepts mastered", "earned": mastered_count >= 5},
        {"icon": "⚡", "label": "Speed Learner", "desc": "No critical concepts", "earned": bool(concepts) and critical_count == 0},
        {"icon": "🏆", "label": "Master", "desc": "All concepts mastered", "earned": bool(concepts) and mastered_count == len(concepts)},
    ]
