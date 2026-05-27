from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core import get_current_user
from app.models import User
from app.schemas.upload import UploadResponse
from app.services.upload_service import build_public_url, save_upload_file

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    response_model=UploadResponse,
    summary="Загрузить изображение",
    description=(
        "Принимает файл (multipart/form-data, поле `file`). "
        "Возвращает публичный URL — его передавайте в logo_url, photos, attachments и т.д."
    ),
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def upload_image(
    _current: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(..., description="Изображение (JPEG, PNG, WebP, GIF)"),
):
    stored_name, content_type, size = await save_upload_file(file)
    return UploadResponse(
        url=build_public_url(stored_name),
        filename=stored_name,
        content_type=content_type,
        size=size,
    )
