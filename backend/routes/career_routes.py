"""
routes/career_routes.py — Career Agent endpoints

POST /career/run/{user_id}    — run career analysis using latest marksheet + analysis
GET  /career/result/{user_id} — get latest saved career recommendation
"""

import json, logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Marksheet, GradeRecord, AnalysisResult, CareerRecommendation
from backend.agents.career_agent import run_career_analysis

router = APIRouter(prefix="/career", tags=["Career Agent"])
logger = logging.getLogger(__name__)


def _get_latest_grades(user_id: int, db: Session) -> list:
    """Fetch grade records from the user's latest marksheet."""
    marksheet = (
        db.query(Marksheet)
        .filter(Marksheet.user_id == user_id)
        .order_by(Marksheet.uploaded_at.desc())
        .first()
    )
    if not marksheet:
        return []
    return [
        {
            "subject":   r.subject,
            "score":     r.score,
            "max_score": r.max_score,
            "grade":     r.grade,
        }
        for r in marksheet.grade_records
    ]


def _get_latest_analysis(user_id: int, db: Session) -> dict:
    """Fetch the most recent saved analysis for a user."""
    record = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not record or not record.summary:
        return {}
    try:
        return json.loads(record.summary)
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────
# POST /career/run/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/run/{user_id}")
def run_career(user_id: int, db: Session = Depends(get_db)):
    """
    Run the Career Agent for a user.
    Requires: at least one marksheet + at least one analysis result.
    Saves result to career_recommendations table.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        grades = _get_latest_grades(user_id, db)
        if not grades:
            raise HTTPException(
                404,
                detail="No marksheet found. Please upload your marksheet first."
            )

        analysis = _get_latest_analysis(user_id, db)
        if not analysis:
            raise HTTPException(
                404,
                detail="No performance analysis found. Please run the AI Analysis on the Analysis page first."
            )

        student_name = user.full_name or user.username

        # Run the career agent
        result = run_career_analysis(grades, analysis, student_name=student_name)

        if "error" in result:
            raise HTTPException(422, detail=result["error"])

        # Save / overwrite
        existing = (
            db.query(CareerRecommendation)
            .filter(CareerRecommendation.user_id == user_id)
            .first()
        )

        if existing:
            existing.careers   = json.dumps(result.get("career_recommendations", []))
            existing.roadmap   = json.dumps(result.get("roadmap", {}))
            existing.reasoning = json.dumps({
                "top_career":         result.get("top_career"),
                "overall_advice":     result.get("overall_advice"),
                "immediate_actions":  result.get("immediate_actions", []),
            })
            db.commit()
        else:
            rec = CareerRecommendation(
                user_id   = user_id,
                careers   = json.dumps(result.get("career_recommendations", [])),
                roadmap   = json.dumps(result.get("roadmap", {})),
                reasoning = json.dumps({
                    "top_career":        result.get("top_career"),
                    "overall_advice":    result.get("overall_advice"),
                    "immediate_actions": result.get("immediate_actions", []),
                }),
            )
            db.add(rec)
            db.commit()

        return {
            "message": "Career analysis complete.",
            "result":  result,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[run_career] {e}", exc_info=True)
        raise HTTPException(500, detail="Career analysis failed unexpectedly. Please try again.")


# ─────────────────────────────────────────────────────────────────
# GET /career/result/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/result/{user_id}")
def get_career_result(user_id: int, db: Session = Depends(get_db)):
    """Return the saved career recommendation for a user."""
    try:
        record = (
            db.query(CareerRecommendation)
            .filter(CareerRecommendation.user_id == user_id)
            .order_by(CareerRecommendation.created_at.desc())
            .first()
        )
        if not record:
            return {"result": None, "message": "No career analysis found. Run the career agent first."}

        careers   = json.loads(record.careers)   if record.careers   else []
        roadmap   = json.loads(record.roadmap)   if record.roadmap   else {}
        reasoning = json.loads(record.reasoning) if record.reasoning else {}

        return {
            "record_id":  record.id,
            "created_at": record.created_at.isoformat(),
            "result": {
                "career_recommendations": careers,
                "roadmap":                roadmap,
                "top_career":             reasoning.get("top_career"),
                "overall_advice":         reasoning.get("overall_advice"),
                "immediate_actions":      reasoning.get("immediate_actions", []),
            },
        }

    except Exception as e:
        logger.error(f"[get_career_result] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch career result.")
