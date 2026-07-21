from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.modules.organisations.models import Department
from resolvehub.app.modules.organisations.service import require_permission
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.tickets.enums import TicketPriority


async def create_category(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    department_id: UUID,
    parent_id: UUID | None,
    name: str,
    description: str | None,
    default_priority: TicketPriority,
) -> ServiceCategory:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="category:create",
    )
    department = await session.scalar(
        select(Department.id).where(
            Department.id == department_id,
            Department.organisation_id == organisation_id,
            Department.is_active.is_(True),
        )
    )
    if department is None:
        raise AppError("DEPARTMENT_NOT_FOUND", "Department was not found.", 404)
    if parent_id and not await session.scalar(
        select(ServiceCategory.id).where(
            ServiceCategory.id == parent_id,
            ServiceCategory.organisation_id == organisation_id,
            ServiceCategory.is_active.is_(True),
        )
    ):
        raise AppError("CATEGORY_PARENT_NOT_FOUND", "Parent category was not found.", 404)
    normalized_name = name.strip()
    if await session.scalar(
        select(ServiceCategory.id).where(
            ServiceCategory.organisation_id == organisation_id,
            ServiceCategory.name == normalized_name,
        )
    ):
        raise AppError("CATEGORY_EXISTS", "A category with this name already exists.", 409)
    category = ServiceCategory(
        organisation_id=organisation_id,
        department_id=department_id,
        parent_id=parent_id,
        name=normalized_name,
        description=description,
        default_priority=default_priority,
    )
    session.add(category)
    await session.commit()
    return category


async def list_categories(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[ServiceCategory]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="organisation:read",
    )
    result = await session.scalars(
        select(ServiceCategory)
        .where(
            ServiceCategory.organisation_id == organisation_id,
            ServiceCategory.is_active.is_(True),
        )
        .order_by(ServiceCategory.name)
        .limit(500)
    )
    return list(result)
