"""
schemas.py — Pydantic request/response models
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from backend.models import UserRole


# ── Auth ─────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username:  str
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None
    role:      Optional[UserRole] = UserRole.student

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v  # no upper limit — pbkdf2_sha256 handles any length


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    role:       UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    message: str
    user:    UserResponse


class RegisterResponse(BaseModel):
    message: str
    user:    UserResponse


# ── OCR / Marksheet ──────────────────────────────────────────────

class GradeItem(BaseModel):
    subject:   str
    score:     Optional[float] = None
    max_score: Optional[float] = 100.0
    grade:     Optional[str]   = None


class MarksheetUploadResponse(BaseModel):
    message:      str
    marksheet_id: int
    grades:       List[GradeItem]
    raw_text:     str


class MarksheetResponse(BaseModel):
    id:         int
    user_id:    int
    file_path:  str
    uploaded_at: datetime
    grades:     List[GradeItem] = []

    model_config = {"from_attributes": True}


# ── Generic ──────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


# ── Analyzer ─────────────────────────────────────────────────────

class SubjectInsight(BaseModel):
    subject:        str
    percentage:     Optional[float] = None
    status:         str              # "weak" | "average" | "strong"
    observation:    str              # why the model flagged this
    recommendation: str              # specific advice for this subject


class AnalyzerRequest(BaseModel):
    marksheet_id: int


class AnalyzerResponse(BaseModel):
    analysis_id:         int
    overall_summary:     str
    performance_pattern: str
    risk_level:          str          # "low" | "medium" | "high"
    weak_subjects:       List[SubjectInsight]
    average_subjects:    List[SubjectInsight]
    strong_subjects:     List[SubjectInsight]
    top_priority:        str
    study_plan_hint:     str
    created_at:          datetime

    model_config = {"from_attributes": True}
