from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }

@router.get("/health/database")
def health_database(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        # Check pg_trgm extension
        trgm_installed = db.execute(
            text("SELECT count(*) FROM pg_extension WHERE extname = 'pg_trgm'")
        ).scalar() > 0
        return {
            "status": "connected",
            "select_1": result == 1,
            "pg_trgm_enabled": bool(trgm_installed),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database connection error: {exc}")
