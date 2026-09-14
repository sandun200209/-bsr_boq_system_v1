import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def find_latest_update_zip(project_root: Path) -> Path | None:
    candidate_dirs = [
        project_root / "data_updates",
        project_root,
        Path.home() / "Downloads"
    ]
    
    found_zips = []
    for d in candidate_dirs:
        if d.exists():
            for f in d.glob("BSR_Data_Update_*.zip"):
                found_zips.append((f.stat().st_mtime, f))
    
    if found_zips:
        found_zips.sort(key=lambda x: x[0], reverse=True)
        return found_zips[0][1]
    
    return None

def import_data_update(zip_path: Path | None = None):
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("=" * 70)
    print("  BSR Rate Hub - Import Data & Document Update Package")
    print("=" * 70)
    print()

    if zip_path is None or not zip_path.exists():
        zip_path = find_latest_update_zip(project_root)

    if zip_path is None or not zip_path.exists():
        print("[ERROR] No 'BSR_Data_Update_*.zip' file was found!")
        print("Please copy the update zip file into the 'data_updates/' or project folder,")
        print("or drag and drop the update zip file onto 'import_data_update.bat'.")
        return False

    print(f"Target Update Package: {zip_path}")
    print()

    # Verify Docker is running
    res = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        print("[ERROR] Docker Desktop is not running! Please start Docker Desktop first.")
        return False

    temp_extract_dir = project_root / "data_updates" / "temp_import"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Extract ZIP
        print("[1/4] Extracting update package...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_extract_dir)

        sql_file = temp_extract_dir / "database.sql"
        if not sql_file.exists():
            print("[ERROR] 'database.sql' missing from update package!")
            return False

        # Step 2: Restore database
        print("[2/4] Restoring PostgreSQL database from update package...")
        cmd = ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "bsr_user", "-d", "bsr_boq"]
        with open(sql_file, "r", encoding="utf-8") as f:
            res = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"[ERROR] Database restore failed: {res.stderr}")
                return False

        print("      Database restored successfully!")

        # Step 3: Copy uploaded source files
        print("[3/4] Merging source documents into data/uploads/...")
        extracted_uploads = temp_extract_dir / "uploads"
        target_uploads = project_root / "data" / "uploads"
        target_uploads.mkdir(parents=True, exist_ok=True)

        if extracted_uploads.exists():
            for root, dirs, files in os.walk(extracted_uploads):
                for file in files:
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(extracted_uploads)
                    dest_file = target_uploads / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
            print("      Source documents merged successfully!")

        # Step 4: Ensure schema & quality
        print("[4/4] Finalizing application sync...")
        subprocess.run(["docker", "compose", "exec", "-T", "backend", "alembic", "upgrade", "head"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "compose", "exec", "-T", "backend", "python", "-m", "app.scripts.clean_noise_and_recalc"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Cleanup
        shutil.rmtree(temp_extract_dir, ignore_errors=True)

        print()
        print("=" * 70)
        print("  DATA & DOCUMENT UPDATE IMPORTED SUCCESSFULLY!")
        print("=" * 70)
        print("All updated rates, uploaded documents, review statuses, and master")
        print("mappings from the source PC are now live on this computer.")
        print()
        print("You can view them immediately at: http://localhost:8080")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"[ERROR] Exception during import: {e}")
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        return False

if __name__ == "__main__":
    zip_arg = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        zip_arg = Path(sys.argv[1]).resolve()
    success = import_data_update(zip_arg)
    if not success:
        sys.exit(1)
