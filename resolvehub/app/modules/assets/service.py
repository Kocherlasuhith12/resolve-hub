import random
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.modules.assets.models import AssetItem
from resolvehub.app.modules.assets.schemas import AssetCreate, AssetUpdate


class AssetService:
    @staticmethod
    async def list_assets(
        session: AsyncSession,
        organisation_id: UUID,
        category: str | None = None,
        search: str | None = None,
    ) -> list[AssetItem]:
        query = select(AssetItem).where(AssetItem.organisation_id == organisation_id)
        if category and category != "ALL":
            query = query.where(AssetItem.category == category)
        if search:
            query = query.where(
                AssetItem.name.ilike(f"%{search}%") | AssetItem.asset_tag.ilike(f"%{search}%")
            )
        query = query.order_by(AssetItem.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_asset(
        session: AsyncSession, organisation_id: UUID, payload: AssetCreate
    ) -> AssetItem:
        tag = f"AST-2026-{random.randint(100, 999)}"
        asset = AssetItem(
            organisation_id=organisation_id,
            asset_tag=tag,
            name=payload.name,
            category=payload.category,
            status=payload.status,
            assigned_to_name=payload.assigned_to_name,
            serial_number=payload.serial_number,
            location=payload.location,
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

    @staticmethod
    async def update_asset(
        session: AsyncSession, organisation_id: UUID, asset_id: UUID, payload: AssetUpdate
    ) -> AssetItem | None:
        query = select(AssetItem).where(
            AssetItem.id == asset_id, AssetItem.organisation_id == organisation_id
        )
        result = await session.execute(query)
        asset = result.scalar_one_or_none()
        if not asset:
            return None

        if payload.name is not None:
            asset.name = payload.name
        if payload.category is not None:
            asset.category = payload.category
        if payload.status is not None:
            asset.status = payload.status
        if payload.assigned_to_name is not None:
            asset.assigned_to_name = payload.assigned_to_name
        if payload.serial_number is not None:
            asset.serial_number = payload.serial_number
        if payload.location is not None:
            asset.location = payload.location

        await session.commit()
        await session.refresh(asset)
        return asset
