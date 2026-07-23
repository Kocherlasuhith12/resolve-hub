from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, status

from resolvehub.app.core.dependencies import AppSettings, CurrentPrincipal, DbSession
from resolvehub.app.modules.organisations.models import Invitation
from resolvehub.app.modules.organisations.schemas import (
    CurrentMembershipResponse,
    DepartmentCreate,
    DepartmentResponse,
    InvitationAccept,
    InvitationCreate,
    InvitationLifecycleResponse,
    InvitationResponse,
    MemberRoleUpdate,
    MembershipDirectoryResponse,
    MembershipResponse,
    MemberStatusUpdate,
    OrganisationCreate,
    OrganisationResponse,
    RoleResponse,
)
from resolvehub.app.modules.organisations.service import (
    accept_invitation,
    create_department,
    create_organisation,
    get_current_membership,
    invite_member,
    list_departments,
    list_invitations,
    list_members,
    list_organisations,
    list_roles,
    resend_invitation,
    revoke_invitation,
    update_member_role,
    update_member_status,
)

router = APIRouter(tags=["Organisations"])


def invitation_status(item: Invitation) -> str:
    if item.accepted_at is not None:
        return "ACCEPTED"
    if item.revoked_at is not None:
        return "REVOKED"
    if item.expires_at <= datetime.now(UTC):
        return "EXPIRED"
    return "PENDING"


def invitation_lifecycle_response(
    item: Invitation, *, invitation_token: str | None = None
) -> InvitationLifecycleResponse:
    return InvitationLifecycleResponse(
        id=item.id,
        email=item.email,
        role_id=item.role_id,
        status=invitation_status(item),
        expires_at=item.expires_at,
        accepted_at=item.accepted_at,
        revoked_at=item.revoked_at,
        created_at=item.created_at,
        invitation_token=invitation_token,
    )


@router.post("/organisations", response_model=OrganisationResponse, status_code=201)
async def organisations_create(
    payload: OrganisationCreate, principal: CurrentPrincipal, session: DbSession
) -> OrganisationResponse:
    organisation = await create_organisation(
        session,
        owner=principal.user,
        name=payload.name,
        slug=payload.slug,
    )
    return OrganisationResponse.model_validate(organisation)


@router.get("/organisations", response_model=list[OrganisationResponse])
async def organisations_list(
    principal: CurrentPrincipal, session: DbSession
) -> list[OrganisationResponse]:
    items = await list_organisations(session, principal.user.id)
    return [OrganisationResponse.model_validate(item) for item in items]


@router.get(
    "/organisations/{organisation_id}/membership/me",
    response_model=CurrentMembershipResponse,
)
async def current_membership_get(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> CurrentMembershipResponse:
    membership = await get_current_membership(session, principal.user.id, organisation_id)
    return CurrentMembershipResponse(
        id=membership.id,
        organisation_id=membership.organisation_id,
        user_id=membership.user_id,
        role_id=membership.role_id,
        role_name=membership.role.name,
        permissions=sorted(permission.code for permission in membership.role.permissions),
    )


@router.get("/organisations/{organisation_id}/roles", response_model=list[RoleResponse])
async def roles_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[RoleResponse]:
    items = await list_roles(session, principal.user.id, organisation_id)
    return [
        RoleResponse(
            id=item.id, name=item.name, permissions=sorted(p.code for p in item.permissions)
        )
        for item in items
    ]


@router.get(
    "/organisations/{organisation_id}/members",
    response_model=list[MembershipDirectoryResponse],
)
async def members_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[MembershipDirectoryResponse]:
    items = await list_members(session, actor_id=principal.user.id, organisation_id=organisation_id)
    return [
        MembershipDirectoryResponse(
            id=membership.id,
            organisation_id=membership.organisation_id,
            user_id=membership.user_id,
            role_id=membership.role_id,
            role_name=membership.role.name,
            display_name=user.display_name,
            email=user.email,
            is_active=membership.is_active,
            created_at=membership.created_at,
        )
        for membership, user in items
    ]


@router.patch(
    "/organisations/{organisation_id}/members/{membership_id}/role",
    response_model=MembershipDirectoryResponse,
)
async def member_role_update(
    organisation_id: UUID,
    membership_id: UUID,
    payload: MemberRoleUpdate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> MembershipDirectoryResponse:
    membership, user = await update_member_role(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        membership_id=membership_id,
        role_id=payload.role_id,
    )
    return MembershipDirectoryResponse(
        id=membership.id,
        organisation_id=membership.organisation_id,
        user_id=membership.user_id,
        role_id=membership.role_id,
        role_name=membership.role.name,
        display_name=user.display_name,
        email=user.email,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.patch(
    "/organisations/{organisation_id}/members/{membership_id}/status",
    response_model=MembershipDirectoryResponse,
)
async def member_status_update(
    organisation_id: UUID,
    membership_id: UUID,
    payload: MemberStatusUpdate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> MembershipDirectoryResponse:
    membership, user = await update_member_status(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        membership_id=membership_id,
        is_active=payload.is_active,
    )
    return MembershipDirectoryResponse(
        id=membership.id,
        organisation_id=membership.organisation_id,
        user_id=membership.user_id,
        role_id=membership.role_id,
        role_name=membership.role.name,
        display_name=user.display_name,
        email=user.email,
        is_active=membership.is_active,
        created_at=membership.created_at,
    )


@router.get(
    "/organisations/{organisation_id}/invitations",
    response_model=list[InvitationLifecycleResponse],
)
async def invitations_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[InvitationLifecycleResponse]:
    items = await list_invitations(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [invitation_lifecycle_response(item) for item in items]


@router.post(
    "/organisations/{organisation_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invitations_create(
    organisation_id: UUID,
    payload: InvitationCreate,
    principal: CurrentPrincipal,
    session: DbSession,
    settings: AppSettings,
) -> InvitationResponse:
    invitation, token = await invite_member(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        email=str(payload.email),
        role_id=payload.role_id,
    )
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        expires_at=invitation.expires_at,
        invitation_token=token if settings.environment in {"local", "test"} else None,
    )


@router.post(
    "/organisations/{organisation_id}/invitations/{invitation_id}/revoke",
    response_model=InvitationLifecycleResponse,
)
async def invitations_revoke(
    organisation_id: UUID,
    invitation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> InvitationLifecycleResponse:
    invitation = await revoke_invitation(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        invitation_id=invitation_id,
    )
    return invitation_lifecycle_response(invitation)


@router.post(
    "/organisations/{organisation_id}/invitations/{invitation_id}/resend",
    response_model=InvitationLifecycleResponse,
)
async def invitations_resend(
    organisation_id: UUID,
    invitation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    settings: AppSettings,
) -> InvitationLifecycleResponse:
    invitation, token = await resend_invitation(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        invitation_id=invitation_id,
    )
    return invitation_lifecycle_response(
        invitation,
        invitation_token=token if settings.environment in {"local", "test"} else None,
    )


@router.post("/invitations/accept", response_model=MembershipResponse)
async def invitations_accept(
    payload: InvitationAccept, principal: CurrentPrincipal, session: DbSession
) -> MembershipResponse:
    membership = await accept_invitation(session, user=principal.user, raw_token=payload.token)
    return MembershipResponse(
        id=membership.id,
        organisation_id=membership.organisation_id,
        user_id=membership.user_id,
        role_id=membership.role_id,
        role_name=membership.role.name,
    )


@router.post(
    "/organisations/{organisation_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def departments_create(
    organisation_id: UUID,
    payload: DepartmentCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> DepartmentResponse:
    department = await create_department(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        name=payload.name,
        description=payload.description,
    )
    return DepartmentResponse.model_validate(department)


@router.get("/organisations/{organisation_id}/departments", response_model=list[DepartmentResponse])
async def departments_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[DepartmentResponse]:
    items = await list_departments(session, principal.user.id, organisation_id)
    return [DepartmentResponse.model_validate(item) for item in items]
