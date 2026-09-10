"""
Database cleanup script for BSR Rate Hub.
Removes calculation noise lines, transitions valid items to VALID,
and synchronizes source file and job statistics.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import select, func, delete, and_, or_
from app.database import SessionLocal
from app.models import RateItem, SourceFile, ImportJob
from app.services.validation_service import is_non_rate_noise

def clean_database():
    db = SessionLocal()
    try:
        print("Starting BSR database cleanup...")

        # 1. Identify and delete pure noise rows
        needs_review_items = db.scalars(
            select(RateItem).where(RateItem.validation_status == "NEEDS_REVIEW")
        ).all()

        noise_ids = []
        valid_ids = []

        for it in needs_review_items:
            desc = it.description or ""
            code = it.item_code
            rate = it.rate
            unit = it.unit

            # If it matches noise criteria
            if is_non_rate_noise(description=desc, code=code, rate=rate, unit=unit):
                noise_ids.append(it.id)
            elif (rate is None or rate <= 0) and not code:
                noise_ids.append(it.id)
            elif rate is not None and 0 < rate <= 50_000_000 and code and desc and len(desc.strip()) >= 3:
                valid_ids.append(it.id)

        print(f"Total NEEDS_REVIEW items inspected: {len(needs_review_items)}")
        print(f"Noise rows to delete: {len(noise_ids)}")
        print(f"Valid items to promote to VALID: {len(valid_ids)}")

        # Delete noise items in batches
        if noise_ids:
            batch_size = 500
            for i in range(0, len(noise_ids), batch_size):
                batch = noise_ids[i:i + batch_size]
                db.execute(delete(RateItem).where(RateItem.id.in_(batch)))
                db.flush()
            print("Successfully deleted noise rows.")

        # Promote valid items in batches
        if valid_ids:
            batch_size = 500
            for i in range(0, len(valid_ids), batch_size):
                batch = valid_ids[i:i + batch_size]
                items_to_update = db.scalars(select(RateItem).where(RateItem.id.in_(batch))).all()
                for item in items_to_update:
                    item.validation_status = "VALID"
                    item.confidence_score = max(item.confidence_score or 0.8, 0.95)
                    # Clean up duplicate code notes if only sheet-level
                    if item.validation_notes and "Duplicate code" in item.validation_notes:
                        item.validation_notes = None
                db.flush()
            print("Successfully promoted valid items to VALID.")

        # Recalculate SourceFile statistics
        source_files = db.scalars(select(SourceFile)).all()
        for sf in source_files:
            total = db.scalar(select(func.count(RateItem.id)).where(RateItem.source_file_id == sf.id)) or 0
            valid = db.scalar(
                select(func.count(RateItem.id)).where(
                    and_(RateItem.source_file_id == sf.id, RateItem.validation_status.in_(["VALID", "APPROVED"]))
                )
            ) or 0
            review = db.scalar(
                select(func.count(RateItem.id)).where(
                    and_(RateItem.source_file_id == sf.id, RateItem.validation_status == "NEEDS_REVIEW")
                )
            ) or 0
            rejected = db.scalar(
                select(func.count(RateItem.id)).where(
                    and_(RateItem.source_file_id == sf.id, RateItem.validation_status == "REJECTED")
                )
            ) or 0

            sf.total_rows_detected = total
            sf.valid_rows = valid
            sf.review_rows = review
            sf.rejected_rows = rejected
            sf.import_status = "READY_FOR_REVIEW" if review > 0 else "COMPLETED"

            # Update latest import job
            job = db.scalar(
                select(ImportJob).where(ImportJob.source_file_id == sf.id).order_by(ImportJob.created_at.desc()).limit(1)
            )
            if job:
                job.message = f"Parsed {total} items ({valid} active, {review} in review, {rejected} rejected)."
                job.status = "COMPLETED"

        db.commit()
        print("Database cleanup and statistics synchronization complete!")

    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
