from __future__ import annotations
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_TITLE: str = "BSR Rate Hub – Sri Lanka BOQ Data System"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://bsr_user:bsr_password@db:5432/bsr_boq"
    )
    
    # Upload & Storage
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
    MAX_UPLOAD_SIZE_BYTES: int = 250 * 1024 * 1024  # 250 MB
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf", ".xlsx", ".xlsm", ".docx", ".csv", ".tsv", ".txt"
    }

    # Sri Lanka Provinces & Districts
    SRI_LANKA_PROVINCES: dict[str, list[str]] = {
        "All Provinces": ["All Districts", "National / All Island"],
        "Western": ["All Districts", "Colombo", "Gampaha", "Kalutara"],
        "Central": ["All Districts", "Kandy", "Matale", "Nuwara Eliya"],
        "Southern": ["All Districts", "Galle", "Matara", "Hambantota"],
        "Northern": ["All Districts", "Jaffna", "Kilinochchi", "Mannar", "Vavuniya", "Mullaitivu"],
        "Eastern": ["All Districts", "Trincomalee", "Batticaloa", "Ampara"],
        "North Western": ["All Districts", "Kurunegala", "Puttalam"],
        "North Central": ["All Districts", "Anuradhapura", "Polonnaruwa"],
        "Uva": ["All Districts", "Badulla", "Monaragala"],
        "Sabaragamuwa": ["All Districts", "Ratnapura", "Kegalle"]
    }

    REVISION_OPTIONS: list[str] = [
        "Original",
        "First Half",
        "Second Half",
        "Revision 01",
        "Revision 02",
        "Final"
    ]

    DATASET_TYPES: list[str] = [
        "BSR Rate Book",
        "Material Rates",
        "Labour Rates",
        "Transport Rates",
        "Other"
    ]

    VAT_BASIS_OPTIONS: list[str] = [
        "With VAT",
        "Without VAT",
        "Not Applicable"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
