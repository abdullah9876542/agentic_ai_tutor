"""
database.py — SQLAlchemy SQLite setup
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

if os.getenv("VERCEL"):
    _default_db = "sqlite:////tmp/data/tutor.db"
else:
    _default_db = "sqlite:///./data/tutor.db"

DATABASE_URL = os.getenv("DATABASE_URL", _default_db)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
