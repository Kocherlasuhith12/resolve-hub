from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.security import generate_opaque_token, hash_opaque_token
from resolvehub.app.modules.identity.models import User
from resolvehub.app.modules.identity.service import normalize_email
from resolvehub.app.modules.organisations.models import (
    Department,
    Invitation,
    Membership,
    Organisation,
    Permission,
    Role,
)
from resolvehub.app.modules.organisations.permissions import (
    ADMIN_PERMISSIONS,
    AGENT_PERMISSIONS,
    AUDITOR_PERMISSIONS,
    REQUESTER_PERMISSIONS,
)

PERMISSION_DESCRIPTIONS = {
    "organisation:read": "Read organisation settings",
    "organisation:update": "Update organisation settings",
    "member:invite": "Invite organisation members",
    "member:read": "Read organisation members",
    "department:create": "Create departments",
    "department:update": "Update departments",
    "category:create": "Create service categories",
    "category:update": "Update service categories",
    "ticket:create": "Create tickets",
    "ticket:read": "Read permitted tickets",
    "ticket:read_all": "Read all organisation tickets",
    "ticket:update": "Update ticket attributes",
    "ticket:assign": "Assign tickets to agents",
    "ticket:transition": "Transition ticket state",
    "ticket:resolve": "Resolve tickets",
    "ticket:reopen": "Reopen resolved tickets",
    "ticket:escalate": "Escalate tickets",
    "comment:create": "Create public comments",
    "internal_note:create": "Create private internal notes",
    "internal_note:read": "Read private internal notes",
    "attachment:create": "Create attachment metadata",
    "audit:view": "Read audit history",
    "sla:manage": "Manage business calendars and SLA policies",
    "notification:read": "Read personal notifications",
    "ai:suggest": "Request optional AI suggestions for accessible tickets",
    "ai:review": "Accept or reject AI suggestions",
}

DEFAULT_ROLE_PERMISSIONS = {
    "Organisation Admin": ADMIN_PERMISSIONS,
    "Agent": AGENT_PERMISSIONS,
    "Requester": REQUESTER_PERMISSIONS,
    "Auditor": AUDITOR_PERMISSIONS,
}


async def require_permission(
    session: AsyncSession, *, user_id: UUID, organisation_id: UUID, permission: str
) -> Membership:
    membership = await session.scalar(
        select(Membership)
        .options(selectinload(Membership.role).selectinload(Role.permissions))
        .where(
            Membership.user_id == user_id,
            Membership.organisation_id == organisation_id,
            Membership.is_active.is_(True),
        )
    )
    if membership is None or permission not in {item.code for item in membership.role.permissions}:
        raise AppError("PERMISSION_DENIED", "You do not have permission for this operation.", 403)
    return membership


def membership_has_permission(membership: Membership, permission: str) -> bool:
    return permission in {item.code for item in membership.role.permissions}


async def create_organisation(
    session: AsyncSession, *, owner: User, name: str, slug: str
) -> Organisation:
    if await session.scalar(select(Organisation.id).where(Organisation.slug == slug)):
        raise AppError("ORGANISATION_SLUG_EXISTS", "Organisation slug is unavailable.", 409)
    organisation = Organisation(name=name.strip(), slug=slug)
    session.add(organisation)
    await session.flush()
    permission_records: dict[str, Permission] = {}
    for code in sorted(set().union(*DEFAULT_ROLE_PERMISSIONS.values())):
        item = await session.scalar(select(Permission).where(Permission.code == code))
        if item is None:
            item = Permission(code=code, description=PERMISSION_DESCRIPTIONS[code])
            session.add(item)
        permission_records[code] = item
    roles: dict[str, Role] = {}
    for role_name, role_permissions in DEFAULT_ROLE_PERMISSIONS.items():
        role = Role(
            organisation_id=organisation.id,
            name=role_name,
            is_system=True,
            permissions=[permission_records[code] for code in sorted(role_permissions)],
        )
        roles[role_name] = role
        session.add(role)
    await session.flush()
    session.add(
        Membership(
            organisation_id=organisation.id,
            user_id=owner.id,
            role_id=roles["Organisation Admin"].id,
        )
    )
    await session.commit()
    return organisation


async def invite_member(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    email: str,
    role_id: UUID,
) -> tuple[Invitation, str]:
    await require_permission(
        session, user_id=actor_id, organisation_id=organisation_id, permission="member:invite"
    )
    role = await session.scalar(
        select(Role).where(Role.id == role_id, Role.organisation_id == organisation_id)
    )
    if role is None:
        raise AppError("ROLE_NOT_FOUND", "Role was not found in this organisation.", 404)
    normalized = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized))
    if user and await session.scalar(
        select(Membership.id).where(
            Membership.organisation_id == organisation_id, Membership.user_id == user.id
        )
    ):
        raise AppError("MEMBERSHIP_EXISTS", "This user is already a member.", 409)
    raw_token = generate_opaque_token()
    invitation = Invitation(
        organisation_id=organisation_id,
        email=normalized,
        role_id=role_id,
        invited_by_id=actor_id,
        token_hash=hash_opaque_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(invitation)
    await session.commit()
    return invitation, raw_token


async def list_members(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[tuple[Membership, User]]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="member:read",
    )
    result = await session.execute(
        select(Membership, User)
        .options(selectinload(Membership.role))
        .join(User, User.id == Membership.user_id)
        .where(Membership.organisation_id == organisation_id)
        .order_by(User.display_name, Membership.id)
        .limit(200)
    )
    return list(result.tuples())


async def list_invitations(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[Invitation]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="member:read",
    )
    return list(
        await session.scalars(
            select(Invitation)
            .where(Invitation.organisation_id == organisation_id)
            .order_by(Invitation.created_at.desc(), Invitation.id.desc())
            .limit(200)
        )
    )


async def revoke_invitation(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    invitation_id: UUID,
) -> Invitation:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="member:invite",
    )
    invitation = await session.scalar(
        select(Invitation)
        .where(
            Invitation.id == invitation_id,
            Invitation.organisation_id == organisation_id,
        )
        .with_for_update()
    )
    if invitation is None:
        raise AppError("INVITATION_NOT_FOUND", "Invitation was not found.", 404)
    if invitation.accepted_at is not None:
        raise AppError(
            "INVITATION_ALREADY_ACCEPTED", "Accepted invitations cannot be revoked.", 409
        )
    invitation.revoked_at = invitation.revoked_at or datetime.now(UTC)
    await session.commit()
    return invitation


async def resend_invitation(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    invitation_id: UUID,
) -> tuple[Invitation, str]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="member:invite",
    )
    invitation = await session.scalar(
        select(Invitation)
        .where(
            Invitation.id == invitation_id,
            Invitation.organisation_id == organisation_id,
        )
        .with_for_update()
    )
    if invitation is None:
        raise AppError("INVITATION_NOT_FOUND", "Invitation was not found.", 404)
    if invitation.accepted_at is not None or invitation.revoked_at is not None:
        raise AppError("INVITATION_NOT_PENDING", "Only pending invitations can be resent.", 409)
    raw_token = generate_opaque_token()
    invitation.token_hash = hash_opaque_token(raw_token)
    invitation.expires_at = datetime.now(UTC) + timedelta(days=7)
    await session.commit()
    return invitation, raw_token


async def accept_invitation(session: AsyncSession, *, user: User, raw_token: str) -> Membership:
    now = datetime.now(UTC)
    invitation = await session.scalar(
        select(Invitation)
        .where(Invitation.token_hash == hash_opaque_token(raw_token))
        .with_for_update()
    )
    if (
        invitation is None
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
        or invitation.email != user.email
    ):
        raise AppError("INVITATION_INVALID", "Invitation is invalid or expired.", 400)
    existing = await session.scalar(
        select(Membership).where(
            Membership.organisation_id == invitation.organisation_id,
            Membership.user_id == user.id,
        )
    )
    if existing:
        raise AppError("MEMBERSHIP_EXISTS", "This user is already a member.", 409)
    membership = Membership(
        organisation_id=invitation.organisation_id,
        user_id=user.id,
        role_id=invitation.role_id,
    )
    invitation.accepted_at = now
    session.add(membership)
    await session.commit()
    await session.refresh(membership, ["role"])
    return membership


async def create_department(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    name: str,
    description: str | None,
) -> Department:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="department:create",
    )
    existing = await session.scalar(
        select(Department.id).where(
            Department.organisation_id == organisation_id, Department.name == name.strip()
        )
    )
    if existing:
        raise AppError("DEPARTMENT_EXISTS", "A department with this name already exists.", 409)
    department = Department(
        organisation_id=organisation_id, name=name.strip(), description=description
    )
    session.add(department)
    await session.commit()
    return department


async def list_organisations(session: AsyncSession, user_id: UUID) -> list[Organisation]:
    result = await session.scalars(
        select(Organisation)
        .join(Membership, Membership.organisation_id == Organisation.id)
        .where(Membership.user_id == user_id, Membership.is_active.is_(True))
        .order_by(Organisation.name)
        .limit(100)
    )
    return list(result)


async def get_current_membership(
    session: AsyncSession, user_id: UUID, organisation_id: UUID
) -> Membership:
    return await require_permission(
        session,
        user_id=user_id,
        organisation_id=organisation_id,
        permission="organisation:read",
    )


async def list_roles(session: AsyncSession, user_id: UUID, organisation_id: UUID) -> list[Role]:
    await require_permission(
        session, user_id=user_id, organisation_id=organisation_id, permission="member:read"
    )
    result = await session.scalars(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.organisation_id == organisation_id)
        .order_by(Role.name)
    )
    return list(result)


async def list_departments(
    session: AsyncSession, user_id: UUID, organisation_id: UUID
) -> list[Department]:
    await require_permission(
        session, user_id=user_id, organisation_id=organisation_id, permission="organisation:read"
    )
    result = await session.scalars(
        select(Department)
        .where(Department.organisation_id == organisation_id)
        .order_by(Department.name)
        .limit(200)
    )
    return list(result)
