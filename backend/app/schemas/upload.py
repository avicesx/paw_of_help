from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    url: str = Field(description="Публичный URL загруженного файла (для logo_url, photos, attachments)")
    filename: str = Field(description="Имя файла на сервере")
    content_type: str
    size: int
