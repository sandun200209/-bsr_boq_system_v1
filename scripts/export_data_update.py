import os
import sys
import time
import json
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime

def export_data_update():
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("=" * 70)
    print("  BSR Rate Hub - Export Data & Document Update Package")
    print("=" * 70)
    print("This packages all uploaded documents, rate updates, master mappings,")
    print("and review data so another PC or laptop can import them immediately.")
    print()

    # Create export directory
    updates_dir = project_root / "data_updates"
    updates_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = updates_dir / f"temp_{timestamp}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    db_dump_file = temp_dir / "database.sql"
    zip_output_file = updates_dir / f"BSR_Data_Update_{timestamp}.zip"

    try:
        # Step 1: Dump database from Docker
        print("[1/3] Dumping database from PostgreSQL container...")
        cmd = ["docker", "compose", "exec", "-T", "postgres", "pg_dump", "-U", "bsr_user", "-d", "bsr_boq"]
        with open(db_dump_file, "w", encoding="utf-8") as f:
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"[ERROR] Database dump failed: {res.stderr}")
                return False

        print(f"      Database dumped successfully ({db_dump_file.stat().st_size / 1024:.1f} KB)")

        # Step 2: Create metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "type": "bsr_data_update",
            "description": "BSR Rate Hub database dump and uploaded documents package"
        }
        meta_file = temp_dir / "update_metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Step 3: Create ZIP package
        print("[2/3] Bundling database and uploaded source documents into ZIP...")
        uploads_dir = project_root / "data" / "uploads"

        with zipfile.ZipFile(zip_output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Add database dump
            zf.write(db_dump_file, arcname="database.sql")
            zf.write(meta_file, arcname="update_metadata.json")

            # Add all uploaded files
            if uploads_dir.exists():
                file_count = 0
                for root, dirs, files in os.walk(uploads_dir):
                    for file in files:
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(uploads_dir)
                        zf.write(full_path, arcname=f"uploads/{rel_path.as_posix()}")
                        file_count += 1
                print(f"      Packaged {file_count} source document files.")

        # Cleanup temp
        if db_dump_file.exists():
            db_dump_file.unlink()
        if meta_file.exists():
            meta_file.unlink()
        temp_dir.rmdir()

        zip_size_mb = zip_output_file.stat().st_size / (1024 * 1024)
        print("[3/3] Update package created successfully!")
        print()
        print("=" * 70)
        print("  DATA UPDATE PACKAGE CREATED!")
        print("=" * 70)
        print(f"Package File:  {zip_output_file}")
        print(f"Package Size:  {zip_size_mb:.2f} MB")
        print()
        print("HOW TO TRANSFER TO ANOTHER PC / LAPTOP:")
        print("  1. Copy this ZIP file to a USB flash drive (or send via email/WhatsApp).")
        print("  2. Paste it on the other laptop into its 'bsr_boq_system_v1' folder.")
        print("  3. On the other laptop, double-click 'import_data_update.bat'.")
        print("  4. The other laptop will immediately see all your uploaded documents and rates!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"[ERROR] Exception during export: {e}")
        return False

if __name__ == "__main__":
    success = export_data_update()
    if not success:
        sys.exit(1)
