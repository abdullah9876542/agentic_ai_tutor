"""
routes/tutor_routes.py — Tutor Agent endpoints (Phase 5)

POST /tutor/start/{user_id}            — start a new session, returns session_id
POST /tutor/chat/{session_id}          — send a message, get tutor response
GET  /tutor/sessions/{user_id}         — list all sessions
GET  /tutor/session/{session_id}       — get full session with messages
DELETE /tutor/session/{session_id}     — end/delete a session
"""

import json, logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Marksheet, GradeRecord, AnalysisResult, TutorSession
from backend.agents.tutor_agent import run_tutor

router = APIRouter(prefix="/tutor", tags=["Tutor Agent"])
logger = logging.getLogger(__name__)


# ── Request schemas ───────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    subject: str = "General"

class ChatRequest(BaseModel):
    message: str
    user_id: int


# ── Helpers ───────────────────────────────────────────────────────

def _build_student_profile(user_id: int, db: Session) -> dict:
    """
    Build student profile from latest analysis result.
    Falls back to empty profile if no analysis exists yet.
    """
    record = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not record or not record.summary:
        return {"weak_subjects": [], "strong_subjects": [], "grade_level": "school/college"}

    try:
        analysis = json.loads(record.summary)
        return {
            "weak_subjects":   analysis.get("weak_subjects", []),
            "strong_subjects": analysis.get("strong_subjects", []),
            "grade_level":     "school/college",
        }
    except Exception:
        return {"weak_subjects": [], "strong_subjects": [], "grade_level": "school/college"}


def _get_weak_subjects(user_id: int, db: Session) -> list:
    """Return list of weak subject names from latest analysis."""
    profile = _build_student_profile(user_id, db)
    return profile.get("weak_subjects", [])


# ─────────────────────────────────────────────────────────────────
# POST /tutor/start/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/start/{user_id}")
def start_session(user_id: int, body: StartSessionRequest, db: Session = Depends(get_db)):
    """Start a new tutoring session. Returns session_id."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        session = TutorSession(
            user_id  = user_id,
            subject  = body.subject.strip(),
            messages = json.dumps([]),   # empty history
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Build initial greeting from tutor
        profile = _build_student_profile(user_id, db)
        result  = run_tutor(
            messages        = [],
            student_profile = profile,
            subject         = body.subject,
        )

        if "error" in result:
            # Session created but greeting failed — return session with fallback message
            greeting = f"Hello! I'm your AI tutor for **{body.subject}**. What would you like to learn today?"
        else:
            greeting = result["response"]

        # Save greeting as first assistant message
        messages = [{"role": "assistant", "content": greeting}]
        session.messages = json.dumps(messages)
        db.commit()

        return {
            "session_id":    session.id,
            "subject":       session.subject,
            "greeting":      greeting,
            "weak_subjects": profile.get("weak_subjects", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[start_session] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not start tutoring session.")


# ─────────────────────────────────────────────────────────────────
# POST /tutor/chat/{session_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/chat/{session_id}")
def chat(session_id: int, body: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to the tutor. Returns tutor response + metadata.
    """
    try:
        session = db.query(TutorSession).filter(TutorSession.id == session_id).first()
        if not session:
            raise HTTPException(404, detail="Session not found.")
        if session.user_id != body.user_id:
            raise HTTPException(403, detail="Session does not belong to this user.")

        # Load conversation history
        try:
            messages = json.loads(session.messages) if session.messages else []
        except Exception:
            messages = []

        # Append student message
        student_msg = body.message.strip()
        if not student_msg:
            raise HTTPException(400, detail="Message cannot be empty.")

        messages.append({"role": "user", "content": student_msg})

        # Build student profile
        profile = _build_student_profile(body.user_id, db)

        # Run tutor agent
        result = run_tutor(
            messages        = messages,
            student_profile = profile,
            subject         = session.subject or "General",
        )

        if "error" in result:
            raise HTTPException(500, detail=result["error"])

        tutor_reply = result["response"]

        # Append tutor reply to history
        messages.append({"role": "assistant", "content": tutor_reply})

        # Save updated history
        session.messages = json.dumps(messages)
        db.commit()

        return {
            "response":       tutor_reply,
            "suggested_quiz": result.get("suggested_quiz", False),
            "topic_complete": result.get("topic_complete", False),
            "input_type":     result.get("input_type", ""),
            "message_count":  len(messages),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[chat] {e}", exc_info=True)
        raise HTTPException(500, detail="Tutor chat failed. Please try again.")


# ─────────────────────────────────────────────────────────────────
# GET /tutor/sessions/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/sessions/{user_id}")
def get_sessions(user_id: int, db: Session = Depends(get_db)):
    """Return all tutor sessions for a user, newest first."""
    try:
        sessions = (
            db.query(TutorSession)
            .filter(TutorSession.user_id == user_id)
            .order_by(TutorSession.started_at.desc())
            .all()
        )
        result = []
        for s in sessions:
            try:
                msgs  = json.loads(s.messages) if s.messages else []
                count = len(msgs)
            except Exception:
                count = 0
            result.append({
                "session_id":    s.id,
                "subject":       s.subject,
                "message_count": count,
                "started_at":    s.started_at.isoformat(),
                "ended_at":      s.ended_at.isoformat() if s.ended_at else None,
            })
        return {"sessions": result, "total": len(result)}

    except Exception as e:
        logger.error(f"[get_sessions] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch sessions.")


# ─────────────────────────────────────────────────────────────────
# GET /tutor/session/{session_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Return full session with all messages."""
    try:
        session = db.query(TutorSession).filter(TutorSession.id == session_id).first()
        if not session:
            raise HTTPException(404, detail="Session not found.")

        messages = json.loads(session.messages) if session.messages else []
        return {
            "session_id": session.id,
            "subject":    session.subject,
            "messages":   messages,
            "started_at": session.started_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_session] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch session.")


# ─────────────────────────────────────────────────────────────────
# GET /tutor/weak-subjects/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/weak-subjects/{user_id}")
def get_weak_subjects(user_id: int, db: Session = Depends(get_db)):
    """Return the student's weak subjects for subject selector in the UI."""
    try:
        weak = _get_weak_subjects(user_id, db)

        # Also get all subjects from latest marksheet
        marksheet = (
            db.query(Marksheet)
            .filter(Marksheet.user_id == user_id)
            .order_by(Marksheet.uploaded_at.desc())
            .first()
        )
        all_subjects = []
        if marksheet:
            all_subjects = [r.subject for r in marksheet.grade_records]

        return {"weak_subjects": weak, "all_subjects": all_subjects}
    except Exception as e:
        logger.error(f"[get_weak_subjects] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch subjects.")
