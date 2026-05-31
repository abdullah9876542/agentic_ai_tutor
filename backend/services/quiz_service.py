"""
services/quiz_service.py — Quiz Generation Service (Phase 6)

Generates 5 MCQ questions for a given subject using GPT-4o.
Scores submitted answers.
Not a full agent — straightforward LLM call with structured output.
"""

import os, json, logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger  = logging.getLogger(__name__)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUIZ_SYSTEM_PROMPT = """
You are an academic quiz generator for school and college students.
Generate exactly 5 multiple-choice questions for the given subject.

Return ONLY valid JSON. No markdown, no explanation, no code fences.

Required structure:
{
  "subject": "Subject name",
  "difficulty": "Easy | Medium | Hard",
  "questions": [
    {
      "id": 1,
      "question": "The question text",
      "options": {
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      },
      "correct_answer": "A",
      "explanation": "Brief explanation of why this answer is correct"
    }
  ]
}

Rules:
- Exactly 5 questions, IDs 1-5.
- Each question must have exactly 4 options (A, B, C, D).
- correct_answer must be A, B, C, or D.
- Questions must be appropriate for school/college level.
- Mix question types: recall, understanding, application.
- Avoid trick questions — test genuine understanding.
"""


def generate_quiz(subject: str, difficulty: str = "Medium",
                  grade_level: str = "school") -> Dict[str, Any]:
    """
    Generate a 5-question MCQ quiz for a subject.
    Returns quiz dict or {"error": "message"}.
    """
    try:
        prompt = (
            f"Generate a {difficulty} difficulty quiz for: {subject}\n"
            f"Student level: {grade_level}\n"
            f"Make questions relevant to Pakistani curriculum if applicable.\n"
            f"Return JSON as specified."
        )

        response = _client.chat.completions.create(
            model       = "gpt-4o",
            max_tokens  = 1500,
            temperature = 0.5,
            messages    = [
                {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("```")).strip()

        quiz = json.loads(raw)

        # Validate structure
        if "questions" not in quiz or len(quiz["questions"]) != 5:
            return {"error": "Quiz generation returned unexpected format. Please try again."}

        return quiz

    except json.JSONDecodeError as e:
        logger.error(f"[generate_quiz] JSON error: {e}")
        return {"error": "GPT returned unexpected format. Please try again."}
    except Exception as e:
        logger.error(f"[generate_quiz] Error: {e}", exc_info=True)
        return {"error": f"Quiz generation failed: {str(e)}"}


def score_quiz(questions: List[Dict], submitted_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Score a submitted quiz.

    Args:
        questions:         List of question dicts with correct_answer
        submitted_answers: {question_id_str: "A"|"B"|"C"|"D"}

    Returns:
        {score, total, percentage, results: [{id, correct, your_answer, correct_answer, explanation}]}
    """
    results = []
    correct_count = 0

    for q in questions:
        qid        = str(q["id"])
        submitted  = submitted_answers.get(qid, "").upper()
        correct    = q.get("correct_answer", "").upper()
        is_correct = submitted == correct

        if is_correct:
            correct_count += 1

        results.append({
            "id":             q["id"],
            "question":       q.get("question", ""),
            "your_answer":    submitted,
            "correct_answer": correct,
            "is_correct":     is_correct,
            "explanation":    q.get("explanation", ""),
        })

    total      = len(questions)
    percentage = round((correct_count / total) * 100, 1) if total > 0 else 0

    if percentage >= 80:   grade = "Excellent"
    elif percentage >= 65: grade = "Good"
    elif percentage >= 50: grade = "Pass"
    else:                  grade = "Needs More Practice"

    return {
        "score":      correct_count,
        "total":      total,
        "percentage": percentage,
        "grade":      grade,
        "results":    results,
    }
