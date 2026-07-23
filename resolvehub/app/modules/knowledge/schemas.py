from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    summary: str = Field("", max_length=1000)
    content_markdown: str = Field(..., min_length=1, max_length=50000)
    category: str = Field("General", max_length=80)
    author_name: str = Field("Support Team", max_length=120)


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_number: str
    organisation_id: UUID
    title: str
    slug: str
    summary: str
    content_markdown: str
    category: str
    author_name: str
    view_count: int
    helpful_count: int
    unhelpful_count: int
    created_at: datetime


class ArticleRateRequest(BaseModel):
    helpful: bool = True
