import os
import sys
import time
import zipfile
from pathlib import Path

def create_full_zip(output_zip_path: Path, project_root: Path):
    print("=" * 70)
    print("  BSR Rate Hub - Full Complete Install Pack ZIP Generator")
    print("=" * 70)
    print(f"Project root: {project_root}")
    print(f"Target ZIP:   {output_zip_path}")
    print()

    # Folders to completely ignore
    IGNORED_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".vscode",
        ".idea",
        "backups",        # skip historical backups in data/backups
        "bsr_boq_system_v1", # empty nested dir
    }

    # Files to ignore
    IGNORED_EXTENSIONS = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".log",
        ".zip",
    }

    start_time = time.time()
    total_files = 0
    total_bytes = 0

    # Ensure target parent directory exists
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Use standard ZIP_DEFLATED with compression level 6 (or fast for large archives)
    with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zip_file:
        for root, dirs, files in os.walk(project_root):
            # Filter directories in-place to avoid recursing into ignored dirs
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            rel_root = Path(root).relative_to(project_root)

            # Skip data/backups specifically
            if "data" in rel_root.parts and "backups" in rel_root.parts:
                continue

            for file in files:
                file_path = Path(root) / file

                # Skip ignored extensions
                if file_path.suffix.lower() in IGNORED_EXTENSIONS:
                    continue

                # Skip any zip files or lock files
                if file.endswith(".zip"):
                    continue

                rel_file_path = file_path.relative_to(project_root)
                # Store inside zip folder 'BSR_Rate_Hub_v1' so when extracted it's nicely contained
                archive_name = Path("BSR_Rate_Hub_v1") / rel_file_path

                file_size = file_path.stat().st_size
                total_bytes += file_size
                total_files += 1

                if file_size > 10 * 1024 * 1024:
                    print(f"Adding large file ({file_size / (1024*1024):.1f} MB): {rel_file_path}...")
                
                zip_file.write(file_path, arcname=str(archive_name))

    elapsed = time.time() - start_time
    zip_size_mb = output_zip_path.stat().st_size / (1024 * 1024)

    print()
    print("=" * 70)
    print("  ZIP PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Output File:     {output_zip_path}")
    print(f"Archive Size:    {zip_size_mb:.2f} MB")
    print(f"Files Packaged:  {total_files:,}")
    print(f"Raw Data Size:   {total_bytes / (1024*1024):.2f} MB")
    print(f"Time Taken:      {elapsed:.1f} seconds")
    print("=" * 70)

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    # Output to Downloads directory
    downloads_dir = Path.home() / "Downloads"
    output_zip = downloads_dir / "BSR_Rate_Hub_Full_Install_Pack_v1.zip"

    if len(sys.argv) > 1:
        output_zip = Path(sys.argv[1]).resolve()

    create_full_zip(output_zip, project_root)
