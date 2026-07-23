from uuid import UUID

from fastapi import APIRouter, status

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.integrations.schemas import (
    APIKeyCreate,
    APIKeyResponse,
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
)
from resolvehub.app.modules.integrations.service import (
    create_api_key,
    create_webhook_subscription,
    delete_webhook_subscription,
    list_api_keys,
    list_webhook_subscriptions,
    revoke_api_key,
    test_ping_webhook,
)

router = APIRouter(prefix="/organisations/{organisation_id}", tags=["Integrations"])


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def api_keys_create(
    organisation_id: UUID,
    payload: APIKeyCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> APIKeyResponse:
    key_record, raw_key = await create_api_key(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        name=payload.name,
        scopes=payload.scopes,
        expires_days=payload.expires_days,
    )
    resp = APIKeyResponse.model_validate(key_record)
    resp.raw_key = raw_key
    return resp


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def api_keys_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[APIKeyResponse]:
    items = await list_api_keys(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [APIKeyResponse.model_validate(item) for item in items]


@router.delete("/api-keys/{key_id}", response_model=APIKeyResponse)
async def api_keys_revoke(
    organisation_id: UUID,
    key_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> APIKeyResponse:
    item = await revoke_api_key(
        session, actor_id=principal.user.id, organisation_id=organisation_id, key_id=key_id
    )
    return APIKeyResponse.model_validate(item)


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def webhooks_create(
    organisation_id: UUID,
    payload: WebhookCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> WebhookResponse:
    sub, raw_secret = await create_webhook_subscription(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        url=str(payload.url),
        events=payload.events,
    )
    resp = WebhookResponse.model_validate(sub)
    resp.raw_secret = raw_secret
    return resp


@router.get("/webhooks", response_model=list[WebhookResponse])
async def webhooks_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[WebhookResponse]:
    items = await list_webhook_subscriptions(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [WebhookResponse.model_validate(item) for item in items]


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def webhooks_delete(
    organisation_id: UUID,
    webhook_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> None:
    await delete_webhook_subscription(
        session, actor_id=principal.user.id, organisation_id=organisation_id, webhook_id=webhook_id
    )


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def webhooks_test_ping(
    organisation_id: UUID,
    webhook_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> WebhookDeliveryResponse:
    delivery = await test_ping_webhook(
        session, actor_id=principal.user.id, organisation_id=organisation_id, webhook_id=webhook_id
    )
    return WebhookDeliveryResponse.model_validate(delivery)
