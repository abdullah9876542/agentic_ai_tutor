"""
routes/quiz_routes.py — Quiz Engine endpoints (Phase 6)

POST /quiz/generate/{user_id}   — generate a quiz for a subject
POST /quiz/submit/{user_id}     — submit answers and get scored
GET  /quiz/history/{user_id}    — list past quiz attempts
GET  /quiz/attempt/{attempt_id} — get a specific attempt with full results
"""

import json, logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict

from backend.database import get_db
from backend.models import User, QuizAttempt
from backend.services.quiz_service import generate_quiz, score_quiz

router = APIRouter(prefix="/quiz", tags=["Quiz Engine"])
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    subject:    str
    difficulty: str = "Medium"    # Easy | Medium | Hard
    grade_level:str = "school"

class SubmitRequest(BaseModel):
    attempt_id: int
    answers:    Dict[str, str]    # {"1": "A", "2": "C", ...}


# ─────────────────────────────────────────────────────────────────
# POST /quiz/generate/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/generate/{user_id}")
def generate(user_id: int, body: GenerateRequest, db: Session = Depends(get_db)):
    """Generate a 5-question MCQ quiz. Saves to DB and returns questions (without answers)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        if not body.subject.strip():
            raise HTTPException(400, detail="Subject is required.")

        quiz = generate_quiz(
            subject     = body.subject.strip(),
            difficulty  = body.difficulty,
            grade_level = body.grade_level,
        )

        if "error" in quiz:
            raise HTTPException(422, detail=quiz["error"])

        # Save attempt (no score yet)
        attempt = QuizAttempt(
            user_id   = user_id,
            subject   = body.subject.strip(),
            questions = json.dumps(quiz["questions"]),  # full Q with answers stored in DB
            score     = None,
            total     = 5,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Return questions WITHOUT correct_answer (hide from frontend during quiz)
        questions_for_ui = []
        for q in quiz["questions"]:
            questions_for_ui.append({
                "id":       q["id"],
                "question": q["question"],
                "options":  q["options"],
            })

        return {
            "attempt_id": attempt.id,
            "subject":    body.subject.strip(),
            "difficulty": body.difficulty,
            "questions":  questions_for_ui,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[generate_quiz] {e}", exc_info=True)
        raise HTTPException(500, detail="Quiz generation failed. Please try again.")


# ─────────────────────────────────────────────────────────────────
# POST /quiz/submit/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/submit/{user_id}")
def submit(user_id: int, body: SubmitRequest, db: Session = Depends(get_db)):
    """Submit answers for a quiz attempt. Returns score + detailed results."""
    try:
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == body.attempt_id,
            QuizAttempt.user_id == user_id,
        ).first()

        if not attempt:
            raise HTTPException(404, detail="Quiz attempt not found.")

        if attempt.score is not None:
            raise HTTPException(400, detail="This quiz has already been submitted.")

        if not body.answers:
            raise HTTPException(400, detail="No answers submitted.")

        # Load stored questions (which have correct_answer)
        questions = json.loads(attempt.questions) if attempt.questions else []
        if not questions:
            raise HTTPException(422, detail="Quiz questions not found. Please generate a new quiz.")

        # Score
        scored = score_quiz(questions, body.answers)

        # Save score
        attempt.score = scored["score"]
        attempt.total = scored["total"]
        db.commit()

        return {
            "attempt_id": attempt.id,
            "subject":    attempt.subject,
            "score":      scored["score"],
            "total":      scored["total"],
            "percentage": scored["percentage"],
            "grade":      scored["grade"],
            "results":    scored["results"],
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[submit_quiz] {e}", exc_info=True)
        raise HTTPException(500, detail="Quiz submission failed. Please try again.")


# ─────────────────────────────────────────────────────────────────
# GET /quiz/history/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    """Return all completed quiz attempts for a user."""
    try:
        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.score != None)
            .order_by(QuizAttempt.attempted_at.desc())
            .all()
        )
        return {
            "attempts": [
                {
                    "attempt_id":   a.id,
                    "subject":      a.subject,
                    "score":        a.score,
                    "total":        a.total,
                    "percentage":   round((a.score / a.total) * 100, 1) if a.total else 0,
                    "attempted_at": a.attempted_at.isoformat(),
                }
                for a in attempts
            ],
            "total": len(attempts),
        }
    except Exception as e:
        logger.error(f"[get_history] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch quiz history.")


# ─────────────────────────────────────────────────────────────────
# GET /quiz/attempt/{attempt_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/attempt/{attempt_id}")
def get_attempt(attempt_id: int, db: Session = Depends(get_db)):
    """Return full attempt with questions and score."""
    try:
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(404, detail="Attempt not found.")

        questions = json.loads(attempt.questions) if attempt.questions else []
        return {
            "attempt_id":   attempt.id,
            "subject":      attempt.subject,
            "score":        attempt.score,
            "total":        attempt.total,
            "attempted_at": attempt.attempted_at.isoformat(),
            "questions":    questions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_attempt] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch attempt.")
