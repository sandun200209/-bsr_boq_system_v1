from __future__ import annotations
import hashlib
import logging
import os
import re
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
import requests
from ..config import settings

logger = logging.getLogger("bsr_rate_hub.storage")

def sanitize_folder_name(name: str) -> str:
    """Sanitize strings for folder names safely across Windows and Linux."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r"\s+", "_", clean.strip())
    return clean or "Unknown"

def sanitize_filename(filename: str) -> str:
    """Sanitize original filename preserving extension."""
    clean = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return clean or "unnamed_file"

def get_media_type(filename: str) -> str:
    """Determine MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".csv": "text/csv",
        ".tsv": "text/tab-separated-values",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".zip": "application/zip",
    }
    return mapping.get(ext, "application/octet-stream")

class StorageService:
    @staticmethod
    def is_supabase_enabled() -> bool:
        """Check if Supabase cloud storage is configured."""
        if settings.STORAGE_BACKEND == "local":
            return False
        return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)

    @classmethod
    def store_uploaded_file(
        cls,
        file: UploadFile,
        province: str,
        district: str,
        year: int,
        revision: str,
    ) -> tuple[Path, str, str, int, str, str, str | None, str | None]:
        """
        Stores original uploaded file either to Supabase Cloud Storage or local disk.
        
        Returns:
            (local_or_cached_path, original_filename, stored_filename, file_size, sha256_hash,
             storage_provider, storage_key, public_url)
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
        storage_key = f"{prov_clean}/{dist_clean}/{year}/{rev_clean}/{stored_filename}"

        hasher = hashlib.sha256()
        file_size = 0

        # Stream file to local disk first (for hashing, extraction, and local cache)
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

        storage_provider = "local"
        public_url = None

        # If Supabase cloud storage is enabled, upload to Supabase Storage bucket
        if cls.is_supabase_enabled():
            try:
                upload_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"
                headers = {
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Content-Type": get_media_type(original_name),
                    "x-upsert": "true",
                }
                with open(stored_path, "rb") as f:
                    res = requests.post(upload_url, headers=headers, data=f, timeout=60)
                
                if res.status_code in [200, 201]:
                    storage_provider = "supabase"
                    public_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"
                    logger.info(f"File uploaded successfully to Supabase Storage: {storage_key}")
                else:
                    logger.warning(f"Supabase Storage upload returned {res.status_code}: {res.text}. Falling back to local storage.")
            except Exception as e:
                logger.warning(f"Failed to upload to Supabase Storage ({e}). Saved locally at {stored_path}.")

        return (
            stored_path,
            original_name,
            stored_filename,
            file_size,
            sha256_hash,
            storage_provider,
            storage_key,
            public_url,
        )

    @classmethod
    def get_file_content_or_path(cls, file_path_str: str, storage_provider: str, storage_key: str | None) -> Path:
        """
        Locates the file on disk or downloads from Supabase Storage if running on a fresh cloud container.
        """
        local_path = Path(file_path_str)
        if local_path.exists():
            return local_path

        # If file is not on local disk and stored on Supabase, download from cloud
        if storage_provider == "supabase" and storage_key and cls.is_supabase_enabled():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            download_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{storage_key}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            }
            res = requests.get(download_url, headers=headers, timeout=60, stream=True)
            if res.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
                return local_path

        raise HTTPException(status_code=404, detail="File could not be found locally or in cloud storage.")

    @classmethod
    def delete_stored_file(cls, file_path_str: str, storage_provider: str, storage_key: str | None) -> bool:
        """Deletes file from both cloud storage and local disk."""
        deleted_local = False
        deleted_cloud = False

        # Delete local copy
        local_path = Path(file_path_str)
        if local_path.exists():
            try:
                local_path.unlink()
                deleted_local = True
            except Exception as e:
                logger.warning(f"Failed to delete local file {local_path}: {e}")

        # Delete cloud copy
        if storage_provider == "supabase" and storage_key and cls.is_supabase_enabled():
            try:
                delete_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}"
                headers = {
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Content-Type": "application/json",
                }
                res = requests.delete(delete_url, headers=headers, json={"prefixes": [storage_key]}, timeout=15)
                if res.status_code == 200:
                    deleted_cloud = True
            except Exception as e:
                logger.warning(f"Failed to delete from Supabase Storage ({storage_key}): {e}")

        return deleted_local or deleted_cloud
