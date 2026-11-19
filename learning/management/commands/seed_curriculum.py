from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import Subject, Concept, Dependency


# Each topic contains:
# (name, description, prerequisite topic numbers)
# Topic numbers start at 1 within each subject.
CURRICULUM = [
    {
        "name": "Data Structures & Algorithms",
        "description": "Organize data and solve problems efficiently.",
        "topics": [
            ("Complexity Analysis",
             "Analyze execution time and memory usage using Big O notation.", []),
            ("Arrays",
             "Practice indexing, traversal, insertion, deletion, and prefix sums.", [1]),
            ("Linked Lists",
             "Build linked lists and implement insertion, deletion, and reversal.", [2]),
            ("Stacks and Queues",
             "Implement LIFO and FIFO structures and solve bracket problems.", [2]),
            ("Recursion",
             "Use base cases and recursive calls to solve smaller subproblems.", [4]),
            ("Searching and Sorting",
             "Implement binary search, insertion sort, merge sort, and quicksort.", [2, 5]),
            ("Trees and Heaps",
             "Implement tree traversals, binary search trees, and priority queues.", [5]),
            ("Graphs",
             "Represent graphs and explore them using BFS and DFS.", [4, 5]),
        ],
    },
    {
        "name": "Python Programming",
        "description": "Learn Python through practical programming exercises.",
        "topics": [
            ("Variables and Data Types",
             "Use numbers, strings, booleans, variables, and type conversions.", []),
            ("Conditions and Loops",
             "Control program flow with conditions, for loops, and while loops.", [1]),
            ("Functions",
             "Write reusable functions with parameters, return values, and scope.", [2]),
            ("Collections",
             "Use lists, tuples, sets, and dictionaries to organize data.", [2]),
            ("Files and Exceptions",
             "Read and write files and handle errors with try and except.", [3, 4]),
            ("Object-Oriented Python",
             "Create classes and use objects, inheritance, and composition.", [3]),
            ("Modules and Environments",
             "Organize modules and isolate dependencies in virtual environments.", [3]),
            ("Testing and Debugging",
             "Write unit tests and diagnose failures using tracebacks.", [5, 6, 7]),
        ],
    },
    {
        "name": "Object-Oriented Programming with Java",
        "description": "Build maintainable programs using Java and OOP.",
        "topics": [
            ("Java Fundamentals",
             "Use Java types, variables, operators, conditions, and loops.", []),
            ("Methods and Arrays",
             "Create methods and process arrays using iteration.", [1]),
            ("Classes and Objects",
             "Define classes, constructors, fields, and instance methods.", [2]),
            ("Encapsulation",
             "Protect object state using access modifiers and validation.", [3]),
            ("Inheritance and Composition",
             "Reuse behavior through inheritance and object composition.", [4]),
            ("Interfaces and Polymorphism",
             "Define contracts and use interchangeable implementations.", [5]),
            ("Exceptions and Collections",
             "Handle exceptions and use generic lists, sets, and maps.", [6]),
            ("OOP Project",
             "Build and test a library system with books, members, and loans.", [7]),
        ],
    },
    {
        "name": "Database Management Systems",
        "description": "Design relational databases and query them using SQL.",
        "topics": [
            ("Relational Database Basics",
             "Understand tables, rows, columns, primary keys, and foreign keys.", []),
            ("Entity Relationship Modeling",
             "Model entities, attributes, relationships, and cardinality.", [1]),
            ("SQL Fundamentals",
             "Create tables and use SELECT, INSERT, UPDATE, and DELETE.", [1]),
            ("Joins and Aggregation",
             "Combine tables and summarize records with GROUP BY.", [3]),
            ("Normalization",
             "Reduce redundancy using functional dependencies and normal forms.", [2]),
            ("Transactions",
             "Understand ACID, commit, rollback, and isolation levels.", [3]),
            ("Indexes and Query Plans",
             "Use indexes and inspect execution plans to improve queries.", [4]),
            ("PostgreSQL Project",
             "Build a course enrollment database with constraints and transactions.", [5, 6, 7]),
        ],
    },
    {
        "name": "Operating Systems",
        "description": "Understand how operating systems manage computing resources.",
        "topics": [
            ("Operating System Fundamentals",
             "Understand kernels, system calls, user mode, and kernel mode.", []),
            ("Processes and Threads",
             "Explain process states, context switching, and multithreading.", [1]),
            ("CPU Scheduling",
             "Compare FCFS, SJF, priority, and round-robin scheduling.", [2]),
            ("Synchronization",
             "Control shared access using mutexes, semaphores, and monitors.", [2]),
            ("Deadlocks",
             "Identify deadlock conditions and compare handling strategies.", [4]),
            ("Memory Management",
             "Understand address spaces, allocation, paging, and segmentation.", [1]),
            ("Virtual Memory",
             "Explain demand paging, page faults, and replacement algorithms.", [6]),
            ("File Systems",
             "Understand directories, file allocation, permissions, and storage.", [1, 6]),
        ],
    },
    {
        "name": "Computer Networks",
        "description": "Learn how devices communicate across networks.",
        "topics": [
            ("Networking Fundamentals",
             "Understand network types, topologies, bandwidth, and latency.", []),
            ("OSI and TCP/IP Models",
             "Explain network layers and encapsulation.", [1]),
            ("Ethernet and Switching",
             "Understand frames, MAC addresses, switches, and ARP.", [2]),
            ("IP Addressing and Subnetting",
             "Practice IPv4 addressing, CIDR, and subnet calculations.", [2]),
            ("Routing",
             "Explain routing tables, default gateways, and packet forwarding.", [3, 4]),
            ("TCP and UDP",
             "Compare reliable streams with connectionless datagrams.", [2, 4]),
            ("DNS and HTTP",
             "Trace name resolution and web request-response exchanges.", [6]),
            ("Network Troubleshooting",
             "Diagnose connectivity using ping, traceroute, and DNS lookup tools.", [5, 7]),
        ],
    },
    {
        "name": "Web Development",
        "description": "Build accessible websites with frontend and backend skills.",
        "topics": [
            ("HTML Fundamentals",
             "Structure pages with semantic elements, forms, and links.", []),
            ("CSS and Responsive Layout",
             "Style pages using the box model, Flexbox, Grid, and media queries.", [1]),
            ("JavaScript Fundamentals",
             "Use variables, functions, arrays, objects, and control flow.", []),
            ("DOM and Events",
             "Update page content and handle user interactions.", [1, 3]),
            ("HTTP and APIs",
             "Understand methods, status codes, JSON, and asynchronous requests.", [3]),
            ("Backend Fundamentals",
             "Build routes, validate input, and render server responses.", [5]),
            ("Authentication and Security",
             "Understand sessions, password hashing, CSRF, and access control.", [6]),
            ("Full-Stack Project",
             "Build a responsive task manager with authentication and CRUD.", [2, 4, 7]),
        ],
    },
    {
        "name": "Software Engineering",
        "description": "Plan, develop, test, and maintain software systematically.",
        "topics": [
            ("Software Development Lifecycle",
             "Understand requirements, design, implementation, testing, and maintenance.", []),
            ("Requirements Engineering",
             "Write user stories and define measurable acceptance criteria.", [1]),
            ("Software Modeling",
             "Describe system behavior and structure using suitable diagrams.", [2]),
            ("Git and Collaboration",
             "Use commits, branches, merges, and pull requests.", [1]),
            ("Software Design",
             "Apply separation of concerns, modularity, and clear interfaces.", [3]),
            ("Software Testing",
             "Plan unit, integration, and acceptance tests.", [2, 5]),
            ("CI/CD Fundamentals",
             "Automate checks, builds, and controlled software releases.", [4, 6]),
            ("Team Project",
             "Deliver a documented application with reviewed changes and tests.", [7]),
        ],
    },
    {
        "name": "Machine Learning Fundamentals",
        "description": "Build and evaluate introductory machine learning models.",
        "topics": [
            ("Python for Data Analysis",
             "Manipulate tabular data and arrays with pandas and NumPy.", []),
            ("Statistics Foundations",
             "Understand averages, variance, probability, and distributions.", []),
            ("Data Preparation",
             "Handle missing values, encode categories, and prevent data leakage.", [1, 2]),
            ("Regression",
             "Train regression models and evaluate numerical predictions.", [3]),
            ("Classification",
             "Train classifiers and interpret precision, recall, and confusion matrices.", [3]),
            ("Model Validation",
             "Use train-test splits and cross-validation to assess generalization.", [4, 5]),
            ("Clustering",
             "Explore unsupervised grouping and feature scaling.", [3]),
            ("Machine Learning Project",
             "Build a reproducible prediction pipeline and document limitations.", [6, 7]),
        ],
    },
    {
        "name": "Cybersecurity Fundamentals",
        "description": "Learn defensive security and responsible testing principles.",
        "topics": [
            ("Security Principles",
             "Understand confidentiality, integrity, availability, and least privilege.", []),
            ("Threat Modeling",
             "Identify assets, trust boundaries, threats, and mitigations.", [1]),
            ("Identity and Access",
             "Understand authentication, authorization, MFA, and account security.", [1]),
            ("Cryptography Basics",
             "Distinguish hashing, encryption, signatures, and key management.", [1]),
            ("Network Defense",
             "Understand firewalls, segmentation, and encrypted communication.", [2]),
            ("Secure Application Design",
             "Apply input validation, safe database queries, and secret management.", [2, 3, 4]),
            ("Logging and Incident Response",
             "Plan useful logs, alerting, containment, and recovery.", [5, 6]),
            ("Defensive Security Review",
             "Review an authorized local application and document remediation.", [7]),
        ],
    },
]


class Command(BaseCommand):
    help = "Add 10 subjects, 80 concepts, and prerequisite relationships."

    @transaction.atomic
    def handle(self, *args, **options):
        created_subjects = 0
        created_concepts = 0
        created_dependencies = 0

        colors = [
            "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4",
            "#6366f1", "#ec4899", "#14b8a6", "#f97316", "#64748b",
        ]

        for subject_index, item in enumerate(CURRICULUM):
            subject, created = Subject.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "icon": "📚",
                    "color": colors[subject_index],
                },
            )
            created_subjects += int(created)

            concepts = {}

            for number, (name, description, prerequisites) in enumerate(
                item["topics"], start=1
            ):
                concept, created = Concept.objects.get_or_create(
                    subject=subject,
                    name=name,
                    defaults={
                        "description": description,
                        "pos_x": 150 + ((number - 1) % 3) * 260,
                        "pos_y": 100 + ((number - 1) // 3) * 180,
                    },
                )
                concepts[number] = concept
                created_concepts += int(created)

            for number, (_, _, prerequisites) in enumerate(
                item["topics"], start=1
            ):
                for prerequisite_number in prerequisites:
                    _, created = Dependency.objects.get_or_create(
                        concept=concepts[number],
                        prerequisite=concepts[prerequisite_number],
                    )
                    created_dependencies += int(created)

            self.stdout.write(f"Ready: {subject.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Added {created_subjects} subjects, "
                f"{created_concepts} concepts, and "
                f"{created_dependencies} prerequisite links."
            )
        )