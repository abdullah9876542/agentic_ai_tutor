"""
routes/analyzer_routes.py — Analyzer Agent endpoints

POST /analyzer/run/{user_id}?marksheet_id=   — run analysis (optional marksheet_id, defaults to latest)
GET  /analyzer/result/{user_id}              — get latest saved analysis for a user
GET  /analyzer/result/marksheet/{id}         — get analysis for a specific marksheet
"""

import json, logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Marksheet, AnalysisResult
from backend.agents.analyzer_agent import run_analysis

router = APIRouter(prefix="/analyzer", tags=["Analyzer Agent"])
logger = logging.getLogger(__name__)


def _grades_from_marksheet(marksheet: Marksheet) -> list:
    return [
        {
            "subject":   r.subject,
            "score":     r.score,
            "max_score": r.max_score,
            "grade":     r.grade,
        }
        for r in marksheet.grade_records
    ]


def _meta_from_marksheet(marksheet: Marksheet) -> dict:
    try:
        return json.loads(marksheet.raw_text) if marksheet.raw_text else {}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────
# POST /analyzer/run/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/run/{user_id}")
def run_analyzer(
    user_id:      int,
    marksheet_id: Optional[int] = Query(default=None, description="Specific marksheet to analyse. Omit to use latest."),
    db:           Session = Depends(get_db),
):
    """
    Run the Analyzer Agent.
    - If marksheet_id is passed, analyses that marksheet.
    - Otherwise analyses the user's most recently uploaded marksheet.
    Saves / overwrites the result in analysis_results and returns full analysis.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        # Resolve which marksheet to analyse
        if marksheet_id:
            marksheet = (
                db.query(Marksheet)
                .filter(Marksheet.id == marksheet_id, Marksheet.user_id == user_id)
                .first()
            )
            if not marksheet:
                raise HTTPException(404, detail="Marksheet not found or does not belong to this user.")
        else:
            marksheet = (
                db.query(Marksheet)
                .filter(Marksheet.user_id == user_id)
                .order_by(Marksheet.uploaded_at.desc())
                .first()
            )
            if not marksheet:
                raise HTTPException(
                    404,
                    detail="No marksheet found. Please upload your marksheet first."
                )

        if not marksheet.grade_records:
            raise HTTPException(
                422,
                detail="This marksheet has no grade records. Please re-upload a clearer image."
            )

        grades       = _grades_from_marksheet(marksheet)
        meta         = _meta_from_marksheet(marksheet)
        student_name = meta.get("student_name") or user.full_name or user.username

        # Run the agent
        analysis = run_analysis(grades, student_name=student_name)

        if "error" in analysis:
            raise HTTPException(422, detail=analysis["error"])

        # Pop internal metrics before saving (metrics are large; analysis is what we store)
        metrics = analysis.pop("_metrics", {})

        # Save or overwrite analysis for this marksheet
        existing = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.user_id      == user_id,
                AnalysisResult.marksheet_id == marksheet.id,
            )
            .first()
        )

        if existing:
            existing.weak_subjects   = json.dumps(analysis.get("weak_subjects", []))
            existing.strong_subjects = json.dumps(analysis.get("strong_subjects", []))
            existing.summary         = json.dumps(analysis)
            db.commit()
        else:
            record = AnalysisResult(
                user_id         = user_id,
                marksheet_id    = marksheet.id,
                weak_subjects   = json.dumps(analysis.get("weak_subjects", [])),
                strong_subjects = json.dumps(analysis.get("strong_subjects", [])),
                summary         = json.dumps(analysis),
            )
            db.add(record)
            db.commit()

        return {
            "message":      "Analysis complete.",
            "marksheet_id": marksheet.id,
            "analysis":     analysis,
            "metrics":      metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[run_analyzer] {e}", exc_info=True)
        raise HTTPException(500, detail="Analyzer failed unexpectedly. Please try again.")


# ─────────────────────────────────────────────────────────────────
# GET /analyzer/result/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/result/{user_id}")
def get_latest_result(user_id: int, db: Session = Depends(get_db)):
    """Return the most recent saved analysis for a user."""
    try:
        record = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.user_id == user_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )
        if not record:
            return {"analysis": None, "message": "No analysis found. Run the analyser first."}

        analysis = json.loads(record.summary) if record.summary else {}
        return {
            "analysis_id":  record.id,
            "marksheet_id": record.marksheet_id,
            "created_at":   record.created_at.isoformat(),
            "analysis":     analysis,
        }

    except Exception as e:
        logger.error(f"[get_latest_result] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch analysis result.")


# ─────────────────────────────────────────────────────────────────
# GET /analyzer/result/marksheet/{marksheet_id}
# NOTE: This route MUST be defined after /result/{user_id} to avoid
#       FastAPI treating "marksheet" as a user_id integer.
# ─────────────────────────────────────────────────────────────────

@router.get("/result/by-marksheet/{marksheet_id}")
def get_result_by_marksheet(marksheet_id: int, db: Session = Depends(get_db)):
    """Return the saved analysis for a specific marksheet."""
    try:
        record = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.marksheet_id == marksheet_id)
            .first()
        )
        if not record:
            return {"analysis": None, "message": "No analysis found for this marksheet."}

        analysis = json.loads(record.summary) if record.summary else {}
        return {
            "analysis_id":  record.id,
            "marksheet_id": marksheet_id,
            "created_at":   record.created_at.isoformat(),
            "analysis":     analysis,
        }

    except Exception as e:
        logger.error(f"[get_result_by_marksheet] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch analysis result.")
