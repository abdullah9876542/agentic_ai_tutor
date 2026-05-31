"""
agents/analyzer_agent.py — Student Performance Analyzer Agent

Architecture:
  LangChain LCEL chain (not LangGraph). Flow is sequential:
  fetch grades → compute metrics (Python) → GPT-4o reasoning → return.
  LangGraph is reserved for Phase 5 Tutor which needs conditional loops.

What it produces:
  summary, performance_level, patterns, weak/average/strong subjects,
  per-subject study recommendations, priority study order,
  motivational note, improvement potential.
"""

import os, json, logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger  = logging.getLogger(__name__)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# Step 1: Plain Python metric computation  (zero LLM cost)
# ─────────────────────────────────────────────────────────────────

def compute_metrics(grades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute performance metrics from grade records.
    Input: [{subject, score, max_score, grade}, ...]
    """
    if not grades:
        return {}

    scored = [g for g in grades if g.get("score") is not None and g.get("max_score")]

    if not scored:
        return {
            "total_subjects":  len(grades),
            "scored_subjects": 0,
            "note": "Only letter grades found, no numeric scores.",
            "grades_only": [g.get("subject") for g in grades],
        }

    subject_stats = []
    for g in scored:
        pct = round((g["score"] / g["max_score"]) * 100, 2)
        if pct >= 80:   tier = "Excellent"
        elif pct >= 65: tier = "Good"
        elif pct >= 50: tier = "Average"
        elif pct >= 35: tier = "Below Average"
        else:           tier = "Fail"

        subject_stats.append({
            "subject":    g["subject"],
            "score":      g["score"],
            "max_score":  g["max_score"],
            "percentage": pct,
            "grade":      g.get("grade"),
            "tier":       tier,
        })

    subject_stats.sort(key=lambda x: x["percentage"])   # weakest first
    pcts = [s["percentage"] for s in subject_stats]

    weak    = [s for s in subject_stats if s["percentage"] < 50]
    average = [s for s in subject_stats if 50 <= s["percentage"] < 70]
    strong  = [s for s in subject_stats if s["percentage"] >= 70]

    return {
        "total_subjects":   len(grades),
        "scored_subjects":  len(scored),
        "average_percent":  round(sum(pcts) / len(pcts), 2),
        "highest_percent":  max(pcts),
        "lowest_percent":   min(pcts),
        "weak_count":       len(weak),
        "average_count":    len(average),
        "strong_count":     len(strong),
        "subject_details":  subject_stats,
        "weak_subjects":    [s["subject"] for s in weak],
        "average_subjects": [s["subject"] for s in average],
        "strong_subjects":  [s["subject"] for s in strong],
    }


# ─────────────────────────────────────────────────────────────────
# Step 2: GPT-4o reasoning
# ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert academic performance analyst and student counsellor.
You receive a student's grade data and computed metrics.
Produce a deep, insightful analysis — not just a restatement of numbers.

Return ONLY valid JSON. No markdown, no explanation, no code fences.

Required JSON structure:
{
  "summary": "2-3 sentence overall summary written warmly and directly to the student.",
  "performance_level": "Excellent | Good | Average | Needs Improvement | Critical",
  "patterns": [
    "Insight about a performance pattern, e.g. strong in language subjects, weak in quantitative ones"
  ],
  "weak_subjects": ["subjects below 50%"],
  "average_subjects": ["subjects 50-69%"],
  "strong_subjects": ["subjects 70%+"],
  "study_recommendations": {
    "SubjectName": "Specific, actionable 1-2 sentence recommendation for this exact subject"
  },
  "priority_study_order": ["SubjectName1 (most urgent)", "SubjectName2", ...],
  "motivational_note": "One encouraging, personalised sentence.",
  "estimated_improvement_potential": "Where the biggest grade gains are possible with focused effort."
}

Rules:
- Mention actual subject names — never give generic advice.
- Failing subjects get top priority in priority_study_order.
- study_recommendations must cover every weak and average subject.
- If all subjects are strong, acknowledge and suggest advanced next steps.
"""


def run_analysis(grades: List[Dict[str, Any]], student_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point. Returns analysis dict or {"error": "message"}.
    """
    if not grades:
        return {"error": "No grade data provided for analysis."}

    try:
        metrics = compute_metrics(grades)
        if not metrics:
            return {"error": "Could not compute metrics from the provided grades."}

        user_content = f"""
Student name: {student_name or 'Not provided'}

Computed metrics:
{json.dumps(metrics, indent=2)}

Full grade records:
{json.dumps(grades, indent=2)}

Analyse this student's performance and return the JSON as instructed.
"""

        response = _client.chat.completions.create(
            model       = "gpt-4o",
            max_tokens  = 2000,
            temperature = 0.4,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ],
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model added them
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("```")).strip()

        result = json.loads(raw)
        result["_metrics"] = metrics   # attach for the route to save
        return result

    except json.JSONDecodeError as e:
        logger.error(f"[analyzer] JSON parse failed: {e}")
        return {"error": "GPT returned an unexpected format. Please try again."}
    except Exception as e:
        logger.error(f"[analyzer] Error: {e}", exc_info=True)
        return {"error": f"Analysis failed: {str(e)}"}
