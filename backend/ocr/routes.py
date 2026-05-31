"""
ocr/routes.py — Marksheet upload and retrieval

POST /ocr/upload/{user_id}        — upload image, extract grades, save to DB
GET  /ocr/marksheets/{user_id}    — list all marksheets for a user
GET  /ocr/marksheet/{marksheet_id} — get single marksheet with grades
"""

import os
import uuid
import json
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Marksheet, GradeRecord
from backend.schemas import MarksheetUploadResponse, MarksheetResponse, GradeItem
from backend.ocr.extractor import extract_grades_from_image
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/ocr", tags=["OCR / Marksheet"])
logger = logging.getLogger(__name__)

UPLOAD_DIR     = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
ALLOWED_EXTS   = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB


# ─────────────────────────────────────────────────────────────────
# POST /ocr/upload/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.post("/upload/{user_id}", response_model=MarksheetUploadResponse)
async def upload_marksheet(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a marksheet image or PDF.
    GPT-4o Vision reads it and extracts subject scores.
    Results are saved to the database.
    """
    try:
        # ── Validate user exists ──────────────────────────────────
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        # ── Validate file type ────────────────────────────────────
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(
                400,
                detail=f"Unsupported file type '{ext}'. Please upload a JPG, PNG, WEBP, or PDF."
            )

        # ── Read and validate file size ───────────────────────────
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(400, detail="The uploaded file is empty.")
        if len(file_bytes) > MAX_SIZE_BYTES:
            raise HTTPException(400, detail="File too large. Maximum size is 10 MB.")

        # ── Save file to disk ─────────────────────────────────────
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        unique_name = f"{user_id}_{uuid.uuid4().hex}{ext}"
        file_path   = os.path.join(UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # ── Extract grades via GPT-4o Vision ──────────────────────
        extraction = extract_grades_from_image(file_path)

        if "error" in extraction:
            # Clean up saved file if extraction failed
            try:
                os.remove(file_path)
            except Exception:
                pass
            raise HTTPException(
                422,
                detail=f"Could not extract grades: {extraction['error']}"
            )

        grades_data = extraction.get("grades", [])
        if not grades_data:
            raise HTTPException(
                422,
                detail="No grades were found in the uploaded image. Please check the file and try again."
            )

        raw_summary = extraction.get("raw_summary", "")

        # ── Save marksheet record ─────────────────────────────────
        marksheet = Marksheet(
            user_id   = user_id,
            file_path = file_path,
            raw_text  = json.dumps({
                "student_name": extraction.get("student_name"),
                "student_id":   extraction.get("student_id"),
                "semester":     extraction.get("semester"),
                "summary":      raw_summary,
            }),
        )
        db.add(marksheet)
        db.flush()  # get marksheet.id before committing

        # ── Save individual grade records ─────────────────────────
        grade_items = []
        for g in grades_data:
            record = GradeRecord(
                marksheet_id = marksheet.id,
                subject      = g["subject"],
                score        = g.get("score"),
                max_score    = g.get("max_score") or 100.0,
                grade        = g.get("grade"),
            )
            db.add(record)
            grade_items.append(GradeItem(
                subject   = g["subject"],
                score     = g.get("score"),
                max_score = g.get("max_score") or 100.0,
                grade     = g.get("grade"),
            ))

        db.commit()

        return MarksheetUploadResponse(
            message      = f"Marksheet uploaded and processed. {len(grade_items)} subjects found.",
            marksheet_id = marksheet.id,
            grades       = grade_items,
            raw_text     = raw_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[upload_marksheet] {e}", exc_info=True)
        raise HTTPException(500, detail="An unexpected error occurred while processing the marksheet.")


# ─────────────────────────────────────────────────────────────────
# GET /ocr/marksheets/{user_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/marksheets/{user_id}")
def get_marksheets(user_id: int, db: Session = Depends(get_db)):
    """Get all marksheets uploaded by a user."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")

        marksheets = (
            db.query(Marksheet)
            .filter(Marksheet.user_id == user_id)
            .order_by(Marksheet.uploaded_at.desc())
            .all()
        )

        result = []
        for ms in marksheets:
            grades = [
                GradeItem(
                    subject   = r.subject,
                    score     = r.score,
                    max_score = r.max_score,
                    grade     = r.grade,
                )
                for r in ms.grade_records
            ]
            result.append({
                "id":          ms.id,
                "user_id":     ms.user_id,
                "file_path":   ms.file_path,
                "uploaded_at": ms.uploaded_at.isoformat(),
                "grades":      [g.model_dump() for g in grades],
            })

        return {"marksheets": result, "total": len(result)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_marksheets] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch marksheets.")


# ─────────────────────────────────────────────────────────────────
# GET /ocr/marksheet/{marksheet_id}
# ─────────────────────────────────────────────────────────────────

@router.get("/marksheet/{marksheet_id}")
def get_marksheet(marksheet_id: int, db: Session = Depends(get_db)):
    """Get a single marksheet with all its grade records."""
    try:
        ms = db.query(Marksheet).filter(Marksheet.id == marksheet_id).first()
        if not ms:
            raise HTTPException(404, detail="Marksheet not found.")

        grades = [
            {
                "subject":   r.subject,
                "score":     r.score,
                "max_score": r.max_score,
                "grade":     r.grade,
            }
            for r in ms.grade_records
        ]

        meta = {}
        if ms.raw_text:
            try:
                meta = json.loads(ms.raw_text)
            except Exception:
                pass

        return {
            "id":           ms.id,
            "user_id":      ms.user_id,
            "uploaded_at":  ms.uploaded_at.isoformat(),
            "student_name": meta.get("student_name"),
            "student_id":   meta.get("student_id"),
            "semester":     meta.get("semester"),
            "summary":      meta.get("summary"),
            "grades":       grades,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_marksheet] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch marksheet details.")
