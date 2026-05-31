"""
services/analytics_service.py — Dashboard data aggregation (Phase 7)
Pure DB queries — no LLM calls.
"""

import json, logging
from sqlalchemy.orm import Session
from backend.models import Marksheet, GradeRecord, AnalysisResult, QuizAttempt, TutorSession

logger = logging.getLogger(__name__)


def get_dashboard_data(user_id: int, db: Session) -> dict:
    """
    Aggregate all stats for a user's dashboard.
    Returns a single dict with everything the frontend needs.
    """
    try:
        # ── Marksheets ────────────────────────────────────────────
        marksheets = (
            db.query(Marksheet)
            .filter(Marksheet.user_id == user_id)
            .order_by(Marksheet.uploaded_at)
            .all()
        )

        marksheet_summaries = []
        all_grades_over_time = []   # for progress chart

        for ms in marksheets:
            grades = [
                {"subject": r.subject, "score": r.score, "max_score": r.max_score}
                for r in ms.grade_records
            ]
            scored = [g for g in grades if g["score"] is not None and g["max_score"]]
            avg    = round(sum(g["score"]/g["max_score"]*100 for g in scored)/len(scored), 1) if scored else None
            marksheet_summaries.append({
                "id":          ms.id,
                "uploaded_at": ms.uploaded_at.isoformat(),
                "subject_count": len(grades),
                "average_pct": avg,
                "grades":      grades,
            })
            if avg is not None:
                all_grades_over_time.append({
                    "date":    ms.uploaded_at.strftime("%d %b %Y"),
                    "average": avg,
                })

        # ── Latest grades per subject ─────────────────────────────
        subject_stats = {}
        if marksheets:
            latest_ms = marksheets[-1]
            for r in latest_ms.grade_records:
                if r.score is not None and r.max_score:
                    pct = round((r.score / r.max_score) * 100, 1)
                    subject_stats[r.subject] = {
                        "subject":    r.subject,
                        "score":      r.score,
                        "max_score":  r.max_score,
                        "percentage": pct,
                        "grade":      r.grade,
                        "tier": "Strong" if pct>=70 else ("Average" if pct>=50 else "Weak"),
                    }

        # ── Latest analysis ───────────────────────────────────────
        analysis_record = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.user_id == user_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )
        latest_analysis = {}
        if analysis_record and analysis_record.summary:
            try:
                latest_analysis = json.loads(analysis_record.summary)
            except Exception:
                pass

        # ── Quiz stats ────────────────────────────────────────────
        quiz_attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.score != None)
            .order_by(QuizAttempt.attempted_at)
            .all()
        )

        quiz_history = []
        quiz_by_subject = {}

        for qa in quiz_attempts:
            pct = round((qa.score / qa.total) * 100, 1) if qa.total else 0
            quiz_history.append({
                "attempt_id":   qa.id,
                "subject":      qa.subject,
                "score":        qa.score,
                "total":        qa.total,
                "percentage":   pct,
                "attempted_at": qa.attempted_at.strftime("%d %b %Y"),
            })
            if qa.subject not in quiz_by_subject:
                quiz_by_subject[qa.subject] = []
            quiz_by_subject[qa.subject].append(pct)

        # Average per subject for quiz performance chart
        quiz_subject_avg = {
            subj: round(sum(scores)/len(scores), 1)
            for subj, scores in quiz_by_subject.items()
        }

        # ── Tutor sessions ────────────────────────────────────────
        sessions = (
            db.query(TutorSession)
            .filter(TutorSession.user_id == user_id)
            .all()
        )
        total_messages = 0
        for s in sessions:
            try:
                msgs = json.loads(s.messages) if s.messages else []
                total_messages += len(msgs)
            except Exception:
                pass

        # ── Summary cards ─────────────────────────────────────────
        total_quizzes      = len(quiz_attempts)
        avg_quiz_score     = round(sum(q["percentage"] for q in quiz_history)/len(quiz_history), 1) if quiz_history else 0
        weak_subjects      = latest_analysis.get("weak_subjects", [])
        strong_subjects    = latest_analysis.get("strong_subjects", [])
        performance_level  = latest_analysis.get("performance_level", "N/A")

        return {
            "summary": {
                "total_marksheets":  len(marksheets),
                "total_quizzes":     total_quizzes,
                "avg_quiz_score":    avg_quiz_score,
                "tutor_sessions":    len(sessions),
                "total_messages":    total_messages,
                "performance_level": performance_level,
                "weak_count":        len(weak_subjects),
                "strong_count":      len(strong_subjects),
            },
            "subject_stats":       list(subject_stats.values()),
            "grades_over_time":    all_grades_over_time,
            "quiz_history":        quiz_history,
            "quiz_subject_avg":    quiz_subject_avg,
            "weak_subjects":       weak_subjects,
            "strong_subjects":     strong_subjects,
            "marksheet_summaries": marksheet_summaries,
        }

    except Exception as e:
        logger.error(f"[get_dashboard_data] {e}", exc_info=True)
        return {"error": str(e)}
