from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# блог организации
class BlogPostCreate(BaseModel):
    title: str
    content: Optional[str] = None
    attachments: List[Any] = []
    tag_ids: List[int] = []


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[Any]] = None
    is_published: Optional[bool] = None


class BlogPostResponse(BaseModel):
    id: int
    organization_id: int
    author_id: int
    title: str
    content: Optional[str] = None
    attachments: List[Any] = []
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BlogCommentCreate(BaseModel):
    content: str


class BlogCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# статьи в базе знаний

class ArticleCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None


class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []
    author_id: Optional[int] = None
    views: int
    published: bool
    likes_count: int
    dislikes_count: int
    rating: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleRatingCreate(BaseModel):
    vote: int  # 1 или -1