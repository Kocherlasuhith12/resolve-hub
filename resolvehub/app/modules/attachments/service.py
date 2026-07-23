from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.audit import log_audit_event
from resolvehub.app.core.database import set_session_organisation_id
from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.storage import StorageProvider, get_storage_provider
from resolvehub.app.modules.attachments.models import Attachment
from resolvehub.app.modules.organisations.service import require_permission
from resolvehub.app.modules.tickets.enums import MalwareScanStatus
from resolvehub.app.modules.tickets.service import (
    ALLOWED_ATTACHMENT_TYPES,
    add_event,
    get_accessible_ticket,
)


async def upload_attachment(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    filename: str,
    content_type: str,
    data: bytes,
    correlation_id: UUID,
    storage: StorageProvider | None = None,
) -> Attachment:
    await set_session_organisation_id(session, organisation_id)
    ticket, _ = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="attachment:create",
    )

    size_bytes = len(data)
    if size_bytes <= 0 or size_bytes > 10_485_760:  # 10MB
        raise AppError(
            "ATTACHMENT_SIZE_INVALID", "Attachment size must be between 1 byte and 10MB.", 422
        )

    safe_name = PurePath(filename).name
    extension = PurePath(safe_name).suffix.casefold()
    if safe_name != filename or content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise AppError("ATTACHMENT_TYPE_FORBIDDEN", "Attachment type is not allowed.", 422)
    if extension not in ALLOWED_ATTACHMENT_TYPES[content_type]:
        raise AppError("ATTACHMENT_TYPE_MISMATCH", "Filename and content type do not match.", 422)

    attachment_id = uuid4()
    storage_key = f"organisations/{organisation_id}/tickets/{ticket_id}/{attachment_id}_{safe_name}"

    provider = storage or get_storage_provider()
    await provider.save_file(storage_key, data, content_type)

    attachment = Attachment(
        id=attachment_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        uploaded_by_id=actor_id,
        original_filename=safe_name,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=size_bytes,
        upload_completed=True,
        scan_status=MalwareScanStatus.CLEAN,
        created_at=datetime.now(UTC),
    )
    session.add(attachment)

    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="ATTACHMENT_UPLOADED",
        correlation_id=correlation_id,
        new_values={
            "attachment_id": str(attachment.id),
            "filename": safe_name,
            "size_bytes": size_bytes,
        },
    )

    log_audit_event(
        action="ATTACHMENT_UPLOADED",
        actor_id=actor_id,
        organisation_id=organisation_id,
        resource_type="attachment",
        resource_id=attachment.id,
        metadata={"filename": safe_name, "size_bytes": size_bytes},
    )

    await session.commit()
    await session.refresh(attachment)
    return attachment


async def list_attachments(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
) -> list[Attachment]:
    await set_session_organisation_id(session, organisation_id)
    await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    items = await session.scalars(
        select(Attachment)
        .where(
            Attachment.organisation_id == organisation_id,
            Attachment.ticket_id == ticket_id,
        )
        .order_by(Attachment.created_at.desc())
    )
    return list(items)


async def download_attachment(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    attachment_id: UUID,
    storage: StorageProvider | None = None,
) -> tuple[Attachment, bytes]:
    await set_session_organisation_id(session, organisation_id)
    await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    attachment = await session.scalar(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.ticket_id == ticket_id,
            Attachment.organisation_id == organisation_id,
        )
    )
    if attachment is None:
        raise AppError("ATTACHMENT_NOT_FOUND", "Attachment was not found.", 404)

    provider = storage or get_storage_provider()
    content = await provider.read_file(attachment.storage_key)
    return attachment, content


async def delete_attachment(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    ticket_id: UUID,
    attachment_id: UUID,
    correlation_id: UUID,
    storage: StorageProvider | None = None,
) -> None:
    await set_session_organisation_id(session, organisation_id)
    ticket, membership = await get_accessible_ticket(
        session,
        actor_id=actor_id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    attachment = await session.scalar(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.ticket_id == ticket_id,
            Attachment.organisation_id == organisation_id,
        )
    )
    if attachment is None:
        raise AppError("ATTACHMENT_NOT_FOUND", "Attachment was not found.", 404)

    # Must be uploaded_by or have admin/agent permission
    if attachment.uploaded_by_id != actor_id and membership.role.name not in {
        "Organisation Admin",
        "Agent",
    }:
        raise AppError(
            "ATTACHMENT_DELETE_FORBIDDEN",
            "You do not have permission to delete this attachment.",
            403,
        )

    provider = storage or get_storage_provider()
    await provider.delete_file(attachment.storage_key)
    await session.delete(attachment)

    add_event(
        session,
        ticket=ticket,
        actor_id=actor_id,
        event_type="ATTACHMENT_DELETED",
        correlation_id=correlation_id,
        previous_values={
            "attachment_id": str(attachment_id),
            "filename": attachment.original_filename,
        },
    )

    log_audit_event(
        action="ATTACHMENT_DELETED",
        actor_id=actor_id,
        organisation_id=organisation_id,
        resource_type="attachment",
        resource_id=attachment_id,
    )

    await session.commit()
