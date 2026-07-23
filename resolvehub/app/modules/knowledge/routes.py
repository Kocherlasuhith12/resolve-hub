from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from resolvehub.app.core.dependencies import DbSession
from resolvehub.app.modules.knowledge.schemas import (
    ArticleCreate,
    ArticleRateRequest,
    ArticleResponse,
)
from resolvehub.app.modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/organisations/{organisation_id}/knowledge/articles", tags=["knowledge"])


@router.get("", response_model=list[ArticleResponse])
async def list_articles(
    organisation_id: UUID,
    session: DbSession,
    category: str | None = None,
    search: str | None = None,
):
    return await KnowledgeService.list_articles(session, organisation_id, category, search)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    organisation_id: UUID,
    article_id: UUID,
    session: DbSession,
):
    article = await KnowledgeService.get_article(session, organisation_id, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    organisation_id: UUID,
    payload: ArticleCreate,
    session: DbSession,
):
    return await KnowledgeService.create_article(session, organisation_id, payload)


@router.post("/{article_id}/rate", response_model=ArticleResponse)
async def rate_article(
    organisation_id: UUID,
    article_id: UUID,
    payload: ArticleRateRequest,
    session: DbSession,
):
    rated = await KnowledgeService.rate_article(
        session, organisation_id, article_id, payload.helpful
    )
    if not rated:
        raise HTTPException(status_code=404, detail="Article not found")
    return rated
