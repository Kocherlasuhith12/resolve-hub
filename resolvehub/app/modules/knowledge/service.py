import random
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.knowledge.models import KnowledgeArticle
from resolvehub.app.modules.knowledge.schemas import ArticleCreate


class KnowledgeService:
    @staticmethod
    async def list_articles(
        session: AsyncSession,
        organisation_id: UUID,
        category: str | None = None,
        search: str | None = None,
    ) -> list[KnowledgeArticle]:
        query = select(KnowledgeArticle).where(KnowledgeArticle.organisation_id == organisation_id)
        if category and category != "ALL":
            query = query.where(KnowledgeArticle.category == category)
        if search:
            query = query.where(
                KnowledgeArticle.title.ilike(f"%{search}%")
                | KnowledgeArticle.content_markdown.ilike(f"%{search}%")
            )
        query = query.order_by(KnowledgeArticle.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_article(
        session: AsyncSession, organisation_id: UUID, article_id: UUID
    ) -> KnowledgeArticle | None:
        query = select(KnowledgeArticle).where(
            KnowledgeArticle.id == article_id, KnowledgeArticle.organisation_id == organisation_id
        )
        result = await session.execute(query)
        article = result.scalar_one_or_none()
        if article:
            article.view_count += 1
            await session.commit()
            await session.refresh(article)
        return article

    @staticmethod
    async def create_article(
        session: AsyncSession, organisation_id: UUID, payload: ArticleCreate
    ) -> KnowledgeArticle:
        number = f"KB-{random.randint(1000, 9999)}"
        slug = re.sub(r"[^\w\s-]", "", payload.title.lower()).strip().replace(" ", "-")
        article = KnowledgeArticle(
            organisation_id=organisation_id,
            article_number=number,
            title=payload.title,
            slug=slug,
            summary=payload.summary,
            content_markdown=payload.content_markdown,
            category=payload.category,
            author_name=payload.author_name,
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)
        return article

    @staticmethod
    async def rate_article(
        session: AsyncSession, organisation_id: UUID, article_id: UUID, helpful: bool
    ) -> KnowledgeArticle | None:
        query = select(KnowledgeArticle).where(
            KnowledgeArticle.id == article_id, KnowledgeArticle.organisation_id == organisation_id
        )
        result = await session.execute(query)
        article = result.scalar_one_or_none()
        if not article:
            return None

        if helpful:
            article.helpful_count += 1
        else:
            article.unhelpful_count += 1

        await session.commit()
        await session.refresh(article)
        return article
