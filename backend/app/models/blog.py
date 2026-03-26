from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)


class OrganizationBlogPost(Base):
    __tablename__ = "organization_blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    author_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    attachments = Column(JSON, default=lambda: [])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, default=False)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderated_by = Column(Integer, nullable=True)


class BlogPostTag(Base):
    __tablename__ = "blog_post_tags"

    post_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, primary_key=True)


class BlogComment(Base):
    __tablename__ = "blog_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=lambda: [])
    author_id = Column(Integer, nullable=True)
    views = Column(Integer, default=0)
    published = Column(Boolean, default=False)
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderated_by = Column(Integer, nullable=True)


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, primary_key=True)


class ArticleRating(Base):
    __tablename__ = "article_ratings"

    article_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    # 1 = лайк, -1 = дизлайк
    vote = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())