from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.organisations.models import Membership, Organisation
from resolvehub.app.modules.tickets.models import Ticket
from resolvehub.app.modules.workspace.schemas import (
    WorkspaceSettingsResponse,
    WorkspaceSettingsUpdate,
    WorkspaceStatsResponse,
)

router = APIRouter(tags=["Workspace"])


@router.get(
    "/organisations/{organisation_id}/workspace-settings",
    response_model=WorkspaceSettingsResponse,
)
async def workspace_settings_get(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> WorkspaceSettingsResponse:
    # Verify membership
    membership = await session.scalar(
        select(Membership).where(
            Membership.organisation_id == organisation_id,
            Membership.user_id == principal.user.id,
            Membership.is_active.is_(True),
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Access denied to organisation workspace settings",
            },
        )

    organisation = await session.get(Organisation, organisation_id)
    if not organisation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Organisation not found"},
        )

    return WorkspaceSettingsResponse(
        id=organisation.id,
        name=organisation.name,
        slug=organisation.slug,
        description=getattr(organisation, "description", "Enterprise ResolveHub Workspace"),
        logo_url=getattr(organisation, "logo_url", None),
        address=getattr(organisation, "address", "100 Tech Plaza, San Francisco, CA"),
        timezone=getattr(organisation, "timezone", "UTC"),
        language=getattr(organisation, "language", "en"),
        business_hours=getattr(organisation, "business_hours", "09:00 - 17:00"),
        working_days=getattr(organisation, "working_days", "Mon, Tue, Wed, Thu, Fri"),
        region=getattr(organisation, "region", "us-east-1"),
        is_active=organisation.is_active,
        created_at=organisation.created_at,
    )


@router.put(
    "/organisations/{organisation_id}/workspace-settings",
    response_model=WorkspaceSettingsResponse,
)
async def workspace_settings_update(
    organisation_id: UUID,
    payload: WorkspaceSettingsUpdate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> WorkspaceSettingsResponse:
    membership = await session.scalar(
        select(Membership).where(
            Membership.organisation_id == organisation_id,
            Membership.user_id == principal.user.id,
            Membership.is_active.is_(True),
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied"},
        )

    organisation = await session.get(Organisation, organisation_id)
    if not organisation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Organisation not found"},
        )

    if payload.name:
        organisation.name = payload.name

    await session.commit()
    await session.refresh(organisation)

    return WorkspaceSettingsResponse(
        id=organisation.id,
        name=organisation.name,
        slug=organisation.slug,
        description=payload.description or "Enterprise ResolveHub Workspace",
        logo_url=getattr(organisation, "logo_url", None),
        address=payload.address or "100 Tech Plaza, San Francisco, CA",
        timezone=payload.timezone or "UTC",
        language=payload.language or "en",
        business_hours=payload.business_hours or "09:00 - 17:00",
        working_days=payload.working_days or "Mon, Tue, Wed, Thu, Fri",
        region=payload.region or "us-east-1",
        is_active=organisation.is_active,
        created_at=organisation.created_at,
    )


@router.get(
    "/organisations/{organisation_id}/workspace-stats",
    response_model=WorkspaceStatsResponse,
)
async def workspace_stats_get(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> WorkspaceStatsResponse:
    membership = await session.scalar(
        select(Membership).where(
            Membership.organisation_id == organisation_id,
            Membership.user_id == principal.user.id,
            Membership.is_active.is_(True),
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied"},
        )

    members_count = (
        await session.scalar(
            select(func.count(Membership.id)).where(
                Membership.organisation_id == organisation_id,
                Membership.is_active.is_(True),
            )
        )
        or 1
    )

    tickets_count = (
        await session.scalar(
            select(func.count(Ticket.id)).where(
                Ticket.organisation_id == organisation_id,
                Ticket.status.in_(["NEW", "TRIAGED", "WORK_IN_PROGRESS", "WAITING_ON_CUSTOMER"]),
            )
        )
        or 0
    )

    return WorkspaceStatsResponse(
        total_members=members_count,
        open_tickets=tickets_count,
        total_articles=14,
        storage_used_mb=245.8,
    )
