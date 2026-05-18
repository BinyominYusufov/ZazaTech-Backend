"""File upload helpers: extension validation, storage, deletion.

Synchronous on purpose — the project uses sync SQLAlchemy and sync route
handlers (FastAPI runs them in a threadpool). An async `aiofiles` version
would force the CRUD endpoints to be `async def`, which would then block the
event loop on the sync SQLite session calls — the exact thing the sync
conversion was done to avoid.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# Root for all uploads; imported by main.py for the StaticFiles mount.
UPLOAD_DIR = Path("uploads")

ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}


def _validated_ext(filename: str | None) -> str:
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension",
        )
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension '.{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXT))}",
        )
    return ext


def save_upload(file: UploadFile, folder: str) -> str:
    """Validate, store under uploads/<folder>/, return the public URL path."""
    ext = _validated_ext(file.filename)

    folder_path = UPLOAD_DIR / folder
    folder_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    destination = folder_path / filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return f"/uploads/{folder}/{filename}"


def delete_file(path: str) -> None:
    """Delete a stored file by its URL path. No-op if absent or path empty."""
    if not path:
        return
    Path(path.lstrip("/")).unlink(missing_ok=True)
