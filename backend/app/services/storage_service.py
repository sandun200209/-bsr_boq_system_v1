from __future__ import annotations
import hashlib
import os
import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from ..config import settings

def sanitize_folder_name(name: str) -> str:
    """Sanitize strings for folder names safely across Windows and Linux."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r"\s+", "_", clean.strip())
    return clean or "Unknown"

def sanitize_filename(filename: str) -> str:
    """Sanitize original filename preserving extension."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return clean or "unnamed_file"

class StorageService:
    @staticmethod
    def store_uploaded_file(
        file: UploadFile,
        province: str,
        district: str,
        year: int,
        revision: str,
    ) -> tuple[Path, str, str, int, str]:
        """
        Stores original uploaded file into structured path:
        /data/uploads/{province}/{district}/{year}/{revision}/{uuid}_{original_filename}
        
        Returns:
            (stored_path, original_filename, stored_filename, file_size, sha256_hash)
        """
        original_name = sanitize_filename(file.filename or "upload")
        ext = Path(original_name).suffix.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}"
            )

        prov_clean = sanitize_folder_name(province)
        dist_clean = sanitize_folder_name(district)
        rev_clean = sanitize_folder_name(revision)

        target_dir = settings.UPLOAD_DIR / prov_clean / dist_clean / str(year) / rev_clean
        target_dir.mkdir(parents=True, exist_ok=True)

        file_uuid = uuid.uuid4().hex
        stored_filename = f"{file_uuid}_{original_name}"
        stored_path = target_dir / stored_filename

        hasher = hashlib.sha256()
        file_size = 0

        # Stream file to disk in chunks to handle up to 250 MB safely without memory exhaustion
        with stored_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)  # 1 MB chunk
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    stored_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                    )
                hasher.update(chunk)
                buffer.write(chunk)

        sha256_hash = hasher.hexdigest()
        return stored_path, original_name, stored_filename, file_size, sha256_hash
