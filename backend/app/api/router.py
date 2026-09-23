from __future__ import annotations
from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .users import router as users_router
from .audit import router as audit_router
from .dashboard import router as dashboard_router
from .documents import router as documents_router
from .rates import router as rates_router
from .compare import router as compare_router
from .review import router as review_router
from .master_items import router as master_items_router
from .export import router as export_router
from .projects import router as projects_router
from .cesmm import router as cesmm_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(audit_router)
api_router.include_router(dashboard_router)
api_router.include_router(documents_router)
api_router.include_router(rates_router)
api_router.include_router(compare_router)
api_router.include_router(review_router)
api_router.include_router(master_items_router)
api_router.include_router(export_router)
api_router.include_router(projects_router)
api_router.include_router(cesmm_router)

