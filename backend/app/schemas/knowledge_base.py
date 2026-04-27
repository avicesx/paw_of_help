from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ArticleListResponse(BaseModel):
    id: int
    title: str
    author_name: str
    created_at: datetime
    views: int
    likes_count: int
    dislikes_count: int
    tags: List[str]

    class Config:
        from_attributes = True


class ArticleDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    author_name: str
    created_at: datetime
    updated_at: Optional[datetime]
    views: int
    tags: List[str]
    liked_by_user: Optional[bool] = None

    class Config:
        from_attributes = True


class ArticleCreateRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = []


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class EncyclopediaCategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BreedResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True