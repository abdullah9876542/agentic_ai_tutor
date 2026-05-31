"""
auth/routes.py — Authentication endpoints

POST /auth/register  — create account
POST /auth/login     — verify credentials
GET  /auth/me/{id}   — fetch user by ID
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import (
    UserRegisterRequest, UserLoginRequest,
    LoginResponse, RegisterResponse, UserResponse,
)
from backend.auth.utils import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(400, detail="Username already taken.")

        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(400, detail="An account with this email already exists.")

        user = User(
            username      = payload.username,
            email         = payload.email,
            password_hash = hash_password(payload.password),
            full_name     = payload.full_name,
            role          = payload.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return RegisterResponse(
            message=f"Account created! Welcome, {user.username}.",
            user=UserResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[register] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not create account. Please try again.")


@router.post("/login", response_model=LoginResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(
            User.username == payload.username.strip().lower()
        ).first()

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(401, detail="Incorrect username or password.")

        return LoginResponse(
            message=f"Welcome back, {user.full_name or user.username}!",
            user=UserResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[login] {e}", exc_info=True)
        raise HTTPException(500, detail="Login failed. Please try again.")


@router.get("/me/{user_id}", response_model=UserResponse)
def get_me(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, detail="User not found.")
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_me] {e}", exc_info=True)
        raise HTTPException(500, detail="Could not fetch user details.")
