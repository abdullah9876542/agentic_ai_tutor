"""
routes/dashboard_routes.py — Dashboard endpoint (Phase 7)
GET /dashboard/{user_id}
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.services.analytics_service import get_dashboard_data

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)


@router.get("/{user_id}")
def dashboard(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")
        data = get_dashboard_data(user_id, db)
        if "error" in data:
            raise HTTPException(500, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[dashboard] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not load dashboard data.")
