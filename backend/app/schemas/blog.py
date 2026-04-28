from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# посты (пользователь/организация)
class PostCreate(BaseModel):
    title: str
    content: Optional[str] = None
    attachments: List[Any] = []
    # если указан organization_id, пост будет опубликован от имени организации (проверка прав в API)
    organization_id: Optional[int] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[List[Any]] = None
    is_published: Optional[bool] = None


class PostResponse(BaseModel):
    id: int
    organization_id: Optional[int] = None
    author_user_id: int
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
    parent_id: Optional[int] = None
    organization_id: Optional[int] = None


class BlogCommentUpdate(BaseModel):
    content: str


class BlogCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int] = None
    organization_id: Optional[int] = None
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    likes: int = 0
    dislikes: int = 0
    my_vote: Optional[int] = None

    class Config:
        from_attributes = True


class CommentReactionRequest(BaseModel):
    vote: int  # 1 (лайк) или -1 (дизлайк); 0 = снять реакцию


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