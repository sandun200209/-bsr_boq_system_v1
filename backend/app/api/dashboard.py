from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SourceFile, RateItem, ImportJob
from ..schemas import SourceFileOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=dict)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_rate_items = db.scalar(select(func.count(RateItem.id))) or 0
    approved_items = db.scalar(select(func.count(RateItem.id)).where(RateItem.validation_status == "APPROVED")) or 0
    items_needing_review = db.scalar(select(func.count(RateItem.id)).where(RateItem.validation_status == "NEEDS_REVIEW")) or 0
    source_files_count = db.scalar(select(func.count(SourceFile.id))) or 0

    provinces_count = db.scalar(select(func.count(func.distinct(RateItem.province)))) or 0
    districts_count = db.scalar(select(func.count(func.distinct(RateItem.district)))) or 0

    # Recent uploads
    recent_files_raw = db.scalars(
        select(SourceFile).order_by(desc(SourceFile.uploaded_at)).limit(5)
    ).all()
    recent_uploads = [SourceFileOut.model_validate(f).model_dump() for f in recent_files_raw]

    # Province breakdown
    province_counts_raw = db.execute(
        select(RateItem.province, func.count(RateItem.id))
        .group_by(RateItem.province)
        .order_by(desc(func.count(RateItem.id)))
        .limit(10)
    ).all()
    province_breakdown = [{"province": p, "count": c} for p, c in province_counts_raw]

    # Latest BSR revisions
    revisions_raw = db.execute(
        select(SourceFile.province, SourceFile.district, SourceFile.year, SourceFile.revision, func.count(SourceFile.id))
        .group_by(SourceFile.province, SourceFile.district, SourceFile.year, SourceFile.revision)
        .order_by(desc(SourceFile.year), SourceFile.province)
        .limit(8)
    ).all()
    latest_revisions = [
        {"province": r[0], "district": r[1], "year": r[2], "revision": r[3], "files": r[4]}
        for r in revisions_raw
    ]

    return {
        "total_rate_items": total_rate_items,
        "approved_items": approved_items,
        "items_needing_review": items_needing_review,
        "source_files_count": source_files_count,
        "provinces_count": provinces_count,
        "districts_count": districts_count,
        "recent_uploads": recent_uploads,
        "province_breakdown": province_breakdown,
        "latest_revisions": latest_revisions,
    }
