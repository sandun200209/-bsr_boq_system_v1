from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import settings
from .database import engine, Base
from .api.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bsr_rate_hub")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables and PostgreSQL extensions exist
    logger.info("Initializing BSR Rate Hub database schemas and extensions...")
    Base.metadata.create_all(bind=engine)

    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_rates_desc_trgm ON rate_items USING gin (description gin_trgm_ops)")
                )
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_rates_code_trgm ON rate_items USING gin (item_code gin_trgm_ops)")
                )
            logger.info("PostgreSQL pg_trgm extension and GIN trigram indexes ready.")
        except Exception as e:
            logger.warning(f"Could not initialize pg_trgm extension or indexes: {e}")

    # Seed CESMM-SL 31 sections and baseline mappings
    try:
        from .database import SessionLocal
        from .services.cesmm_service import seed_cesmm_sections
        with SessionLocal() as db:
            seed_cesmm_sections(db)
        logger.info("CESMM-SL 31 Work Sections checked/initialized.")
    except Exception as e:
        logger.warning(f"Could not initialize CESMM-SL sections: {e}")

    yield

    # Shutdown
    logger.info("Shutting down BSR Rate Hub application...")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Sri Lanka Construction BSR Rate Data Management System",
    lifespan=lifespan,
)

# Enable CORS for multi-PC LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {str(exc)}"}
    )

# Mount all API endpoints under /api
app.include_router(api_router, prefix=settings.API_PREFIX)

# Serve built React frontend if dist exists (enables running natively without Docker/Nginx)
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
