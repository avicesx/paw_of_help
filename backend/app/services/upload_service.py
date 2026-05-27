import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.core import settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def get_upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def max_upload_bytes() -> int:
    return settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024


def build_public_url(stored_name: str) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    media_path = settings.MEDIA_URL_PATH.strip("/")
    return f"{base}/{media_path}/{stored_name}"


async def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    """Сохраняет изображение и возвращает (stored_name, content_type, size)."""
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допустимы только изображения: JPEG, PNG, WebP, GIF",
        )

    data = await file.read()
    size = len(data)
    if size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой файл")
    if size > max_upload_bytes():
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой (максимум {settings.UPLOAD_MAX_SIZE_MB} МБ)",
        )

    ext = ALLOWED_CONTENT_TYPES[content_type]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = get_upload_dir() / stored_name
    dest.write_bytes(data)

    return stored_name, content_type, size
