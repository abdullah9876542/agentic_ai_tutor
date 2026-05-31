"""
agents/career_agent.py — Career & Roadmap Agent (Phase 4)
Enhanced: detects grade level, provides education pathway, Pakistan context.
"""

import os, json, logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger  = logging.getLogger(__name__)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


CAREER_SYSTEM_PROMPT = """
You are an expert career counsellor and academic advisor specialising in the Pakistani education system.
You receive a student's subject grades, their performance level, and AI analysis.

FIRST: Identify the student's current education level from the subjects:
- If subjects include Islamiyat, Pakistan Studies, Urdu, and science/math at basic level → Matric (Grade 9-10)
- If subjects include FSc/ICS/ICom style subjects → Intermediate (Grade 11-12)  
- If O/A Level style → O-Levels or A-Levels
- Otherwise infer from subject names and complexity

Return ONLY valid JSON. No markdown, no explanation, no code fences.

Required JSON structure:
{
  "detected_grade_level": "Matric | Intermediate | O-Levels | A-Levels | Other",
  "education_pathway": {
    "current_level": "e.g. Matric (Grade 10)",
    "next_steps": [
      "Step 1: e.g. After Matric, choose between Pre-Medical, Pre-Engineering, ICS, or Arts for Intermediate",
      "Step 2: e.g. After Intermediate, apply to relevant universities",
      "Step 3: e.g. Degree path based on career choice"
    ],
    "recommended_stream": "e.g. Pre-Engineering or ICS for technology careers",
    "timeline": "e.g. 2 years Intermediate → 4 years degree = 6 years to career"
  },
  "career_recommendations": [
    {
      "title": "Specific Career Title (e.g. Software Engineer, Doctor, Business Analyst)",
      "field": "Broad field (Technology / Medicine / Business / Arts / Sciences / Law / Education)",
      "match_score": 85,
      "match_reasoning": "2-3 sentences explaining why this suits the student based on actual grades",
      "required_subjects_now": ["Subjects student must improve at current level"],
      "university_subjects": ["Subjects needed at degree level"],
      "skill_gaps": ["Specific gap based on weak subjects"],
      "degree_options": ["e.g. BS Computer Science from FAST, LUMS, NUST", "BSc from University of Karachi"],
      "job_roles": ["Entry-level role", "Mid-level role", "Senior role"],
      "salary_range_pkr": "e.g. 80,000 - 250,000 PKR/month for entry to senior",
      "resources": [
        {"name": "Resource name", "type": "Course/Book/YouTube/Platform", "url": "actual URL or 'Search: keyword'"}
      ]
    }
  ],
  "top_career": "Title of the best-matched career",
  "roadmap": {
    "career": "Top career title",
    "total_weeks": 8,
    "goal": "Concrete goal achievable in 8 weeks at current education level",
    "weeks": [
      {
        "week": 1,
        "theme": "Week theme",
        "focus_subjects": ["Subject1"],
        "tasks": ["Task 1", "Task 2", "Task 3"],
        "milestone": "What student can do by end of this week"
      }
    ]
  },
  "overall_advice": "2-3 sentences of honest, direct advice based on actual scores and Pakistani academic context.",
  "immediate_actions": [
    "Concrete action 1 to take this week",
    "Concrete action 2",
    "Concrete action 3"
  ]
}

Rules:
- match_score must be a number 0-100.
- Recommend exactly 3 career paths — best match first.
- ALL recommendations must be grounded in ACTUAL subject grades provided.
- If science scores are weak, do NOT recommend medicine as top career.
- roadmap must have exactly 8 weeks, each with exactly 3 tasks.
- Tailor advice to Pakistani universities, job market, and education system.
- immediate_actions must be exactly 3 specific, actionable things.
- salary_range_pkr must be realistic for the Pakistani market.
"""


def run_career_analysis(
    grades:       List[Dict[str, Any]],
    analysis:     Dict[str, Any],
    student_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run career analysis. Returns full result dict or {"error": "message"}.
    Requires grades + Phase 3 analysis output.
    """
    if not grades:
        return {"error": "No grade data provided."}

    try:
        user_content = f"""
Student name: {student_name or 'Not provided'}

Subject grades (use these to detect education level and build recommendations):
{json.dumps(grades, indent=2)}

AI Performance Analysis results:
- Overall performance level: {analysis.get('performance_level', 'Unknown')}
- Strong subjects: {analysis.get('strong_subjects', [])}
- Weak subjects: {analysis.get('weak_subjects', [])}
- Average subjects: {analysis.get('average_subjects', [])}
- Performance patterns: {analysis.get('patterns', [])}
- Summary: {analysis.get('summary', '')}

Instructions:
1. First detect what grade/level this marksheet is from based on subject names.
2. Provide a clear education pathway from current level to career entry.
3. Recommend 3 careers based on actual scores — be honest about mismatches.
4. Generate an 8-week roadmap for the top matched career at the student's current level.

Return JSON exactly as specified.
"""

        response = _client.chat.completions.create(
            model       = "gpt-4o",
            max_tokens  = 3500,
            temperature = 0.4,
            messages    = [
                {"role": "system", "content": CAREER_SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ],
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("```")).strip()

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.error(f"[career_agent] JSON parse error: {e}")
        return {"error": "GPT returned an unexpected format. Please try again."}
    except Exception as e:
        logger.error(f"[career_agent] Error: {e}", exc_info=True)
        return {"error": f"Career analysis failed: {str(e)}"}
