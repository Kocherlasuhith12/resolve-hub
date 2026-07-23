from uuid import UUID, uuid4

from fastapi import APIRouter, File, Header, Response, UploadFile, status

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.attachments.schemas import AttachmentResponse
from resolvehub.app.modules.attachments.service import (
    delete_attachment,
    download_attachment,
    list_attachments,
    upload_attachment,
)

router = APIRouter(tags=["Attachments"])


@router.post(
    "/organisations/{organisation_id}/tickets/{ticket_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attachment_upload(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    file: UploadFile = File(...),
    x_request_id: UUID | None = Header(default=None),
) -> AttachmentResponse:
    content = await file.read()
    attachment = await upload_attachment(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        filename=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
        data=content,
        correlation_id=x_request_id or uuid4(),
    )
    return AttachmentResponse.model_validate(attachment)


@router.get(
    "/organisations/{organisation_id}/tickets/{ticket_id}/attachments",
    response_model=list[AttachmentResponse],
)
async def attachments_list(
    organisation_id: UUID,
    ticket_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> list[AttachmentResponse]:
    items = await list_attachments(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
    )
    return [AttachmentResponse.model_validate(item) for item in items]


@router.get(
    "/organisations/{organisation_id}/tickets/{ticket_id}/attachments/{attachment_id}/download",
)
async def attachment_download(
    organisation_id: UUID,
    ticket_id: UUID,
    attachment_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> Response:
    attachment, content = await download_attachment(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
    )
    return Response(
        content=content,
        media_type=attachment.content_type,
        headers={"Content-Disposition": f'attachment; filename="{attachment.original_filename}"'},
    )


@router.delete(
    "/organisations/{organisation_id}/tickets/{ticket_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def attachment_delete(
    organisation_id: UUID,
    ticket_id: UUID,
    attachment_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    x_request_id: UUID | None = Header(default=None),
) -> None:
    await delete_attachment(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        ticket_id=ticket_id,
        attachment_id=attachment_id,
        correlation_id=x_request_id or uuid4(),
    )
