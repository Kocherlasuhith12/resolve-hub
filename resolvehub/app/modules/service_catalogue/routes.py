from uuid import UUID

from fastapi import APIRouter, status

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.service_catalogue.schemas import CategoryCreate, CategoryResponse
from resolvehub.app.modules.service_catalogue.service import create_category, list_categories

router = APIRouter(prefix="/organisations/{organisation_id}/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def categories_create(
    organisation_id: UUID,
    payload: CategoryCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> CategoryResponse:
    category = await create_category(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        department_id=payload.department_id,
        parent_id=payload.parent_id,
        name=payload.name,
        description=payload.description,
        default_priority=payload.default_priority,
    )
    return CategoryResponse.model_validate(category)


@router.get("", response_model=list[CategoryResponse])
async def categories_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[CategoryResponse]:
    items = await list_categories(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [CategoryResponse.model_validate(item) for item in items]
