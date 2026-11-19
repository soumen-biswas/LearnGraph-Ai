"""
AI Engine — LearnGraph
Groq API (Free, Fast, No billing required)

Setup:
    pip install groq
    set GROQ_API_KEY=gsk_your_key_here  (Windows)
    export GROQ_API_KEY=gsk_your_key_here  (Mac/Linux)

Get free key: https://console.groq.com
"""
import json
from groq import Groq
from django.conf import settings

MODEL = settings.GROQ_MODEL  # Free, fast


class AIConfigurationError(ValueError):
    pass

def _client():
    key = getattr(settings, 'GROQ_API_KEY', '')
    if not key or key == 'your-groq-key-here':
        raise AIConfigurationError('GROQ_API_KEY not set in the environment — get free key from https://console.groq.com')
    return Groq(api_key=key, timeout=30.0, max_retries=1)


def _completion(**kwargs):
    from academy.telemetry import record_completion
    return record_completion(lambda: _client().chat.completions.create(**kwargs), kwargs.get('model', MODEL), 'chat.completions')


def _call(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call Groq and return text."""
    response = _completion(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_json(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call Groq and return cleaned JSON string."""
    text = _call(system, user, max_tokens)
    text = text.replace("```json", "").replace("```", "").strip()
    return text


# ── 1. QUIZ GENERATOR ─────────────────────────────────────────────────────────
def generate_quiz(concept_name: str, subject_name: str, num_questions: int = 5) -> list:
    """
    Quiz Generator Prompt:
        Generate 5 MCQ questions about Stack Data Structure.
        Include: Question, 4 options, Correct answer, Difficulty level
    """
    system = "You are a CS quiz generator. Return ONLY valid JSON arrays, no explanation, no markdown."
    user = f"""Generate {num_questions} MCQ questions about "{concept_name}" in {subject_name}.

Return ONLY this JSON array format:
[
  {{
    "question": "What is the time complexity of push in a Stack?",
    "option_a": "O(n)",
    "option_b": "O(log n)",
    "option_c": "O(1)",
    "option_d": "O(n^2)",
    "correct_answer": "c",
    "difficulty": "easy",
    "explanation": "Explain why the correct option is right in 1-3 sentences"
  }}
]

correct_answer must be lowercase: a, b, c, or d
difficulty must be: easy, medium, or hard"""

    raw = _call_json(system, user)
    return json.loads(raw)


# ── 2. LEARNING SUGGESTION ────────────────────────────────────────────────────
def get_learning_suggestion(concept_name: str, mastery: int) -> dict:
    """
    Learning Suggestion Prompt:
        Student weak in Stack. Suggest:
        - Learning strategy, Practice advice, Common mistakes
    Resources are always hardcoded — AI never generates URLs (they are fake).
    """
    level = "beginner" if mastery < 25 else "struggling" if mastery < 50 else "intermediate"
    system = "You are a CS learning advisor. Return ONLY valid JSON, no explanation, no markdown."
    user = f"""A university CS student is {level} in "{concept_name}" (mastery: {mastery}%).

Return ONLY this JSON — do NOT include any URLs, only fill strategy, practice, mistakes, estimated_days:
{{
  "strategy": "Specific 2-3 sentence strategy for learning {concept_name} from scratch to advanced",
  "practice": "Specific practice advice — what exercises, how many problems, which patterns to focus on",
  "mistakes": [
    "Most common mistake students make with {concept_name}",
    "Second common mistake to avoid",
    "Third common mistake to avoid"
  ],
  "estimated_days": 7
}}"""

    raw = _call_json(system, user)
    data = json.loads(raw)

    # Always build resources ourselves — never trust AI for URLs
    from urllib.parse import quote_plus
    q = quote_plus(concept_name)
    data["resources"] = [
        {
            "name": f"YouTube — {concept_name} Tutorial",
            "type": "📺 Video",
            "url": f"https://www.youtube.com/results?search_query={q}+tutorial+explained",
        },
        {
            "name": f"GeeksForGeeks — {concept_name}",
            "type": "📖 Article",
            "url": f"https://www.geeksforgeeks.org/?s={q}",
        },
        {
            "name": f"LeetCode — {concept_name} Problems",
            "type": "💻 Practice",
            "url": f"https://leetcode.com/problemset/?search={q}&difficulty=EASY",
        },
        {
            "name": "W3Schools — CS Reference",
            "type": "📚 Reference",
            "url": "https://www.w3schools.com/dsa/index.php",
        },
        {
            "name": "CS50 Harvard — Free Course",
            "type": "🎓 Course",
            "url": "https://cs50.harvard.edu/x/",
        },
    ]

    return data


# ── 3. CHATBOT ────────────────────────────────────────────────────────────────
def chat_with_tutor(user_message: str, subject: str, history: list) -> str:
    """
    Chatbot — works like Claude, answers anything.
    Supports multi-turn conversation history.
    """
    system = f"""You are LearnGraph AI — a brilliant, friendly CS tutor for university students.
The student is studying: "{subject}".

Your personality:
- Crystal clear explanations with real-world examples
- Use code in triple backticks when helpful
- Be encouraging and honest
- Answer ANYTHING the student asks — not limited to CS
- Keep answers focused (3-5 paragraphs max)

CRITICAL LANGUAGE RULE — follow exactly:
- Student writes in English → reply in English
- Student writes in Bengali (বাংলা) → reply in Bengali  
- Student writes in Banglish (Bengali using English letters, e.g. "ki korbo", "explain koro", "kemon acho") → reply in Banglish
- NEVER switch language on your own — always match the student exactly"""

    # Build messages with history
    messages = [{"role": "system", "content": system}]
    for msg in history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": user_message})

    response = _completion(
        model=MODEL,
        max_tokens=1500,
        temperature=0.7,
        messages=messages,
    )
    return response.choices[0].message.content.strip()


# ── 4. LEARNING PATH GENERATOR ────────────────────────────────────────────────
def generate_learning_path(subject_name: str, weak_concepts: list, strong_concepts: list) -> dict:
    """Generate a personalized step-by-step learning path."""
    weak_str = ", ".join([f"{c['name']} ({c['mastery']}%)" for c in weak_concepts])
    strong_str = ", ".join([c["name"] for c in strong_concepts]) if strong_concepts else "None yet"

    system = "You are a learning path generator. Return ONLY valid JSON, no explanation, no markdown."
    user = f"""Student studying {subject_name}.
Weak (mastery < 50%): {weak_str}
Strong (mastery >= 70%): {strong_str}

Return ONLY this JSON:
{{
  "summary": "2-sentence personalized overview",
  "estimated_days": 14,
  "path": [
    {{
      "step": 1,
      "concept": "Concept name",
      "action": "Specific what to do",
      "time": "3-4 hours",
      "priority": "High",
      "resource": "Specific resource",
      "tip": "One pro tip"
    }}
  ]
}}

Generate exactly 6 steps. Priority must be High, Medium, or Low."""

    raw = _call_json(system, user)
    return json.loads(raw)


# ── 5. AI RECOMMENDATIONS ─────────────────────────────────────────────────────
def get_ai_recommendations(subject_name: str, concepts_data: list) -> dict:
    """Get AI-powered recommendations for the dashboard."""
    concepts_str = "\n".join([f"- {c['name']}: {c['mastery']}%" for c in concepts_data])
    avg = round(sum(c['mastery'] for c in concepts_data) / len(concepts_data)) if concepts_data else 0

    system = "You are a learning analytics AI. Return ONLY valid JSON, no explanation, no markdown."
    user = f"""Student's {subject_name} progress (avg: {avg}%):
{concepts_str}

Return ONLY this JSON:
{{
  "prediction": "2-sentence performance prediction",
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2",
    "Actionable recommendation 3"
  ],
  "predicted_score": {avg},
  "bottlenecks": ["Weakest concept 1", "Weakest concept 2"],
  "weekly_plan": [
    "Day 1: Topic and task",
    "Day 2: Topic and task",
    "Day 3: Topic and task",
    "Day 4: Topic and task",
    "Day 5: Topic and task",
    "Day 6: Review and practice",
    "Day 7: Mock test"
  ]
}}"""

    raw = _call_json(system, user)
    return json.loads(raw)


# ── 6. PREREQUISITE AUTO-GENERATOR ───────────────────────────────────────────
def generate_prerequisites(concept_name: str, subject_name: str, all_concepts: list) -> list:
    """Auto-detect prerequisites from existing concept list."""
    system = "You are a CS curriculum expert. Return ONLY a JSON array, no explanation."
    user = f"""In {subject_name}, which of these are direct prerequisites for "{concept_name}"?
Available: {", ".join(all_concepts)}
Return ONLY: ["concept1", "concept2"] or [] if none."""

    raw = _call_json(system, user, max_tokens=200)
    return json.loads(raw)