"""
models.py — All database table definitions
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50),  unique=True, nullable=False, index=True)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(100), nullable=True)
    role          = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    marksheets     = relationship("Marksheet",     back_populates="owner",   cascade="all, delete")
    tutor_sessions = relationship("TutorSession",  back_populates="student", cascade="all, delete")


class Marksheet(Base):
    __tablename__ = "marksheets"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path   = Column(String(255), nullable=False)
    raw_text    = Column(Text,        nullable=True)   # raw GPT extraction output
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner         = relationship("User",        back_populates="marksheets")
    grade_records = relationship("GradeRecord", back_populates="marksheet", cascade="all, delete")


class GradeRecord(Base):
    __tablename__ = "grade_records"

    id           = Column(Integer, primary_key=True, index=True)
    marksheet_id = Column(Integer, ForeignKey("marksheets.id"), nullable=False)
    subject      = Column(String(100), nullable=False)
    score        = Column(Float,       nullable=True)
    max_score    = Column(Float,       nullable=True, default=100.0)
    grade        = Column(String(5),   nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    marksheet = relationship("Marksheet", back_populates="grade_records")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    marksheet_id    = Column(Integer, ForeignKey("marksheets.id"), nullable=False)
    weak_subjects   = Column(Text, nullable=True)   # JSON list
    strong_subjects = Column(Text, nullable=True)   # JSON list
    summary         = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    careers    = Column(Text, nullable=True)   # JSON list
    roadmap    = Column(Text, nullable=True)   # JSON
    reasoning  = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TutorSession(Base):
    __tablename__ = "tutor_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject    = Column(String(100), nullable=True)
    messages   = Column(Text, nullable=True)   # JSON list of {role, content}
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at   = Column(DateTime, nullable=True)

    student = relationship("User", back_populates="tutor_sessions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject      = Column(String(100), nullable=False)
    questions    = Column(Text,  nullable=True)   # JSON
    score        = Column(Float, nullable=True)
    total        = Column(Integer, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow)
