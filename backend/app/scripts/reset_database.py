"""
Full Database Reset Script for BSR Rate Hub.
Clears all rate items, source files, import jobs, master items, and mappings.
Resets database sequences to 1 and cleans the uploads storage directory.
"""
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import settings

def reset_database(clear_uploads: bool = True):
    print(=========================================================)
    print( BSR Rate Hub - Full Database Reset & Clean)
    print(=========================================================)

    # 1. Truncate all data tables with CASCADE and RESTART IDENTITY
    tables_to_truncate = [
        rate_item_master_mapping,
        rate_items,
        master_items,
        import_jobs,
        source_files
    ]
    
    with engine.begin() as conn:
        print(fTruncating tables: {', '.join(tables_to_truncate)}...)
        conn.execute(
            text(fTRUNCATE TABLE {', '.join(tables_to_truncate)} RESTART IDENTITY CASCADE;)
        )
        print(Database tables truncated and sequences reset to 1.)

    # 2. Clean uploaded files directory
    if clear_uploads:
        upload_path = Path(settings.UPLOAD_DIR)
        print(fCleaning upload directory: {upload_path}...)
        if upload_path.exists():
            for item in upload_path.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    print(fWarning: Could not remove {item}: {e})
            print(Upload directory cleaned.)
        else:
            upload_path.mkdir(parents=True, exist_ok=True)
            print(Upload directory created.)

    print(\nDatabase is now completely clean and ready for fresh imports!)
    print(=========================================================)

if __name__ == __main__:
    reset_database()
