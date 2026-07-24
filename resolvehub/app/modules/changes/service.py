import random
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.database import set_session_organisation_id
from resolvehub.app.modules.changes.models import ChangeRequest
from resolvehub.app.modules.changes.schemas import ChangeCreate, ChangeUpdate


class ChangeService:
    @staticmethod
    async def list_changes(session: AsyncSession, organisation_id: UUID) -> list[ChangeRequest]:
        await set_session_organisation_id(session, organisation_id)
        query = (
            select(ChangeRequest)
            .where(ChangeRequest.organisation_id == organisation_id)
            .order_by(ChangeRequest.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_change(
        session: AsyncSession, organisation_id: UUID, payload: ChangeCreate
    ) -> ChangeRequest:
        await set_session_organisation_id(session, organisation_id)
        number = f"CHG-2026-{random.randint(100, 999)}"
        change = ChangeRequest(
            organisation_id=organisation_id,
            change_number=number,
            title=payload.title,
            description=payload.description,
            change_type=payload.change_type,
            risk_level=payload.risk_level,
            owner_name=payload.owner_name,
            maintenance_window=payload.maintenance_window,
            status="CAB Approval",
        )
        session.add(change)
        await session.commit()
        await session.refresh(change)
        return change

    @staticmethod
    async def update_change(
        session: AsyncSession, organisation_id: UUID, change_id: UUID, payload: ChangeUpdate
    ) -> ChangeRequest | None:
        query = select(ChangeRequest).where(
            ChangeRequest.id == change_id, ChangeRequest.organisation_id == organisation_id
        )
        result = await session.execute(query)
        change = result.scalar_one_or_none()
        if not change:
            return None

        if payload.title is not None:
            change.title = payload.title
        if payload.description is not None:
            change.description = payload.description
        if payload.change_type is not None:
            change.change_type = payload.change_type
        if payload.risk_level is not None:
            change.risk_level = payload.risk_level
        if payload.status is not None:
            change.status = payload.status
        if payload.owner_name is not None:
            change.owner_name = payload.owner_name
        if payload.maintenance_window is not None:
            change.maintenance_window = payload.maintenance_window

        await session.commit()
        await session.refresh(change)
        return change
