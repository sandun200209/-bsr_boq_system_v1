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

    SUPPORTED_SECTORS: list[str] = [
        "Building Works",
        "Highway / Road Works",
        "Water Supply Works",
        "Sewerage Works",
        "Storm Water Drainage Works",
        "Other"
    ]

    SUPPORTED_RATE_SYSTEMS: list[str] = [
        "BSR",
        "HSR",
        "Water Supply Rates",
        "Sewerage & Storm Water Drainage Works",
        "Other / Custom"
    ]

    SECTOR_RATE_SYSTEM_MAP: dict[str, list[str]] = {
        "Building Works": ["BSR"],
        "Highway / Road Works": ["HSR"],
        "Water Supply Works": ["Water Supply Rates"],
        "Sewerage Works": ["Sewerage & Storm Water Drainage Works"],
        "Storm Water Drainage Works": ["Sewerage & Storm Water Drainage Works"],
        "Other": ["Other / Custom", "BSR", "HSR", "Water Supply Rates", "Sewerage & Storm Water Drainage Works"]
    }

    SECTOR_CATEGORY_PRESETS: dict[str, list[str]] = {
        "Building Works": [
            "Demolition & Alterations", "Earthwork & Excavation", "Concrete Work", 
            "Masonry & Brickwork", "Roofing & Cladding", "Carpentry & Joinery", 
            "Plumbing & Drainage", "Electrical Installation", "Floor & Wall Finishes", 
            "Painting & Decorating", "Metalwork & Ironmongery", "External Works"
        ],
        "Highway / Road Works": [
            "Site Clearing & Earthwork", "Subbase, Base & Shoulder Construction", 
            "Bituminous Surfacing & Asphalt", "Road Drainage Structures", 
            "Bridges & Precast Culverts", "Traffic Safety, Signs & Road Marking", 
            "Retaining Walls & Gabions", "Incidental Road Works"
        ],
        "Water Supply Works": [
            "Ductile Iron (DI) Pipes & Fittings", "HDPE / MDPE Pipes & Fittings", 
            "uPVC Pipes & Pressure Fittings", "Valves, Hydrants & Flow Meters", 
            "Pumping Machinery, Motors & Controls", "Water Treatment Plant Equipment", 
            "Ground & Elevated Water Reservoirs", "Customer Service Connections", 
            "Hydrostatic Pressure Testing & Disinfection"
        ],
        "Sewerage Works": [
            "Gravity Sewer Collection Mains", "Sewer Manholes & Drop Chambers", 
            "Wastewater Pumping Stations & Force Mains", "Screening & Grit Chambers", 
            "Aeration, Sedimentation & Treatment Tanks", "Sludge Dewatering & Drying Beds", 
            "Odor Control Systems & Effluent Disposal"
        ],
        "Storm Water Drainage Works": [
            "Open Lined & Unlined Surface Drains", "Precast Concrete U-Drains & Covers", 
            "Box Culverts & Circular Pipe Culverts", "Inlet Pits, Catch Basins & Gullies", 
            "Channel Excavation & River Training", "Flood Retention Basins & Sluice Gates", 
            "Erosion Control & Gabion Mattresses"
        ],
        "Other": ["General Works", "Provisional Sums", "Prime Cost Items", "Miscellaneous"]
    }

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
