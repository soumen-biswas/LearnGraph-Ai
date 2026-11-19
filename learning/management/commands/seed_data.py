"""
Management command to seed the database with sample data.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from learning.models import Subject, Concept, Dependency


SEED_DATA = {
    "Data Structures": {
        "icon": "⬡", "color": "#3b82f6",
        "concepts": [
            ("Arrays",       90, 350, 60),
            ("Linked List",  75, 180, 170),
            ("Stack",        60, 350, 170),
            ("Queue",        55, 520, 170),
            ("Hash Table",   50, 680, 170),
            ("Binary Tree",  40, 220, 290),
            ("BST",          30, 110, 390),
            ("Heap",         20, 330, 390),
            ("Graph",        10, 510, 340),
            ("Trie",          5, 660, 390),
        ],
        "edges": [
            ("Arrays", "Linked List"),
            ("Arrays", "Stack"),
            ("Arrays", "Queue"),
            ("Arrays", "Hash Table"),
            ("Linked List", "Binary Tree"),
            ("Binary Tree", "BST"),
            ("Binary Tree", "Heap"),
            ("Queue", "Graph"),
            ("Binary Tree", "Trie"),
        ],
    },
    "Algorithms": {
        "icon": "◈", "color": "#8b5cf6",
        "concepts": [
            ("Time Complexity", 80, 360, 60),
            ("Sorting",         70, 180, 170),
            ("Searching",       65, 360, 170),
            ("Recursion",       55, 540, 170),
            ("Greedy",          35, 100, 300),
            ("BFS",             40, 280, 300),
            ("DFS",             38, 460, 300),
            ("Dynamic Prog",    25, 620, 300),
            ("Dijkstra",        15, 370, 410),
            ("KMP",             10, 570, 410),
        ],
        "edges": [
            ("Time Complexity", "Sorting"),
            ("Time Complexity", "Searching"),
            ("Time Complexity", "Recursion"),
            ("Sorting", "Greedy"),
            ("Searching", "BFS"),
            ("Recursion", "DFS"),
            ("Recursion", "Dynamic Prog"),
            ("BFS", "Dijkstra"),
            ("Dynamic Prog", "KMP"),
        ],
    },
    "Machine Learning": {
        "icon": "◎", "color": "#06b6d4",
        "concepts": [
            ("Statistics",    85, 200, 60),
            ("Linear Algebra",78, 520, 60),
            ("Regression",    65, 360, 160),
            ("Classification",50, 200, 270),
            ("Clustering",    40, 520, 270),
            ("Neural Nets",   30, 360, 270),
            ("CNN",           20, 180, 380),
            ("RNN",           15, 360, 380),
            ("Transformer",   10, 540, 380),
            ("Reinforcement Learning", 8, 360, 460),
        ],
        "edges": [
            ("Statistics", "Regression"),
            ("Linear Algebra", "Regression"),
            ("Regression", "Classification"),
            ("Statistics", "Clustering"),
            ("Linear Algebra", "Neural Nets"),
            ("Classification", "CNN"),
            ("Neural Nets", "RNN"),
            ("RNN", "Transformer"),
            ("Neural Nets", "Reinforcement Learning"),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed database with sample subjects, concepts and dependencies"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding database...")

        for subject_name, data in SEED_DATA.items():
            subject, created = Subject.objects.get_or_create(
                name=subject_name,
                defaults={"icon": data["icon"], "color": data["color"]}
            )
            if created:
                self.stdout.write(f"  ✅ Created subject: {subject_name}")
            else:
                self.stdout.write(f"  ⏭  Subject exists: {subject_name}")

            concept_map = {}
            for name, mastery, x, y in data["concepts"]:
                c, _ = Concept.objects.get_or_create(
                    subject=subject, name=name,
                    defaults={"mastery": mastery, "pos_x": x, "pos_y": y}
                )
                concept_map[name] = c

            for from_name, to_name in data["edges"]:
                if from_name in concept_map and to_name in concept_map:
                    Dependency.objects.get_or_create(
                        concept=concept_map[to_name],
                        prerequisite=concept_map[from_name],
                    )

        self.stdout.write(self.style.SUCCESS("\n✅ Database seeded successfully!"))
        self.stdout.write("   Now run: python manage.py runserver")
