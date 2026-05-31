"""
routes/notification_routes.py — Notification endpoints (Phase 8)

POST /notify/send-report/{user_id}   — build and email a full performance report
GET  /notify/preview/{user_id}       — preview the report data without sending
"""

import json, logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    User, Marksheet, GradeRecord,
    AnalysisResult, CareerRecommendation, QuizAttempt, TutorSession
)
from backend.services.notification_service import send_report_email

router = APIRouter(prefix="/notify", tags=["Notifications"])
logger = logging.getLogger(__name__)


def _build_report(user_id: int, user: User, db: Session) -> dict:
    """
    Aggregate all student data into a single report dict
    used by both the email sender and the preview endpoint.
    """
    # ── Latest marksheet grades ───────────────────────────────────
    marksheet = (
        db.query(Marksheet)
        .filter(Marksheet.user_id == user_id)
        .order_by(Marksheet.uploaded_at.desc())
        .first()
    )
    subject_grades = []
    if marksheet:
        subject_grades = [
            {"subject": r.subject, "score": r.score,
             "max_score": r.max_score, "grade": r.grade}
            for r in marksheet.grade_records
        ]

    # ── Latest AI analysis ────────────────────────────────────────
    analysis_record = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    analysis = {}
    if analysis_record and analysis_record.summary:
        try:
            analysis = json.loads(analysis_record.summary)
        except Exception:
            pass

    # ── Career recommendation ─────────────────────────────────────
    career_record = (
        db.query(CareerRecommendation)
        .filter(CareerRecommendation.user_id == user_id)
        .order_by(CareerRecommendation.created_at.desc())
        .first()
    )
    top_career        = ""
    immediate_actions = []
    if career_record:
        try:
            reasoning         = json.loads(career_record.reasoning) if career_record.reasoning else {}
            top_career        = reasoning.get("top_career", "")
            immediate_actions = reasoning.get("immediate_actions", [])
        except Exception:
            pass

    # ── Quiz stats ────────────────────────────────────────────────
    quiz_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id, QuizAttempt.score != None)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
        .all()
    )
    quiz_history = [
        {
            "subject":      q.subject,
            "score":        q.score,
            "total":        q.total,
            "percentage":   round((q.score / q.total) * 100, 1) if q.total else 0,
            "attempted_at": q.attempted_at.strftime("%d %b %Y"),
        }
        for q in quiz_attempts
    ]
    total_quizzes  = len(quiz_history)
    avg_quiz_score = (
        round(sum(q["percentage"] for q in quiz_history) / len(quiz_history), 1)
        if quiz_history else 0
    )

    # ── Tutor sessions ────────────────────────────────────────────
    tutor_count = db.query(TutorSession).filter(TutorSession.user_id == user_id).count()

    return {
        "student_name":      user.full_name or user.username,
        "email":             user.email,
        "performance_level": analysis.get("performance_level", "N/A"),
        "summary":           analysis.get("summary", "No analysis available yet. Please run AI Analysis first."),
        "weak_subjects":     analysis.get("weak_subjects", []),
        "average_subjects":  analysis.get("average_subjects", []),
        "strong_subjects":   analysis.get("strong_subjects", []),
        "patterns":          analysis.get("patterns", []),
        "study_recommendations": analysis.get("study_recommendations", {}),
        "motivational_note": analysis.get("motivational_note", ""),
        "subject_grades":    subject_grades,
        "quiz_history":      quiz_history,
        "total_quizzes":     total_quizzes,
        "avg_quiz_score":    avg_quiz_score,
        "tutor_sessions":    tutor_count,
        "top_career":        top_career,
        "immediate_actions": immediate_actions,
    }


# ─────────────────────────────────────────────────────────────────
# POST /notify/send-report/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/send-report/{user_id}")
def send_report(user_id: int, db: Session = Depends(get_db)):
    """
    Build a full performance report and send it to the student's registered email.
    The email is sent to the same address used during registration.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        if not user.email:
            raise HTTPException(400, detail="No email address on file for this user.")

        report = _build_report(user_id, user, db)

        result = send_report_email(
            to_email     = user.email,
            student_name = report["student_name"],
            report       = report,
        )

        if not result["success"]:
            raise HTTPException(500, detail=result["error"])

        return {
            "message":  f"Report sent successfully to {user.email}",
            "sent_to":  user.email,
            "student":  report["student_name"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[send_report] {e}", exc_info=True)
        raise HTTPException(500, detail="Failed to send report. Please try again.")


# ─────────────────────────────────────────────────────────────────
# GET /notify/preview/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/preview/{user_id}")
def preview_report(user_id: int, db: Session = Depends(get_db)):
    """
    Return the report data without sending an email.
    Used by the frontend to show what will be sent before confirming.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")
        report = _build_report(user_id, user, db)
        return {"report": report, "will_send_to": user.email}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[preview_report] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not build report preview.")
