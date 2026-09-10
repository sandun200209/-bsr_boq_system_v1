from __future__ import annotations
import logging
from contextlib import asynccontextmanager
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
