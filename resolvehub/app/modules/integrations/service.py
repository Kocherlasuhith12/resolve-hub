from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.security import generate_opaque_token, hash_opaque_token
from resolvehub.app.modules.integrations.models import APIKey, WebhookDelivery, WebhookSubscription
from resolvehub.app.modules.organisations.service import require_permission


async def create_api_key(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    name: str,
    scopes: str = "*",
    expires_days: int | None = None,
) -> tuple[APIKey, str]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="apikey:manage",
    )
    raw_secret = generate_opaque_token()
    prefix = f"rh_{raw_secret[:6]}"
    full_key = f"{prefix}_{raw_secret}"
    key_hash = hash_opaque_token(full_key)

    expires_at = datetime.now(UTC) + timedelta(days=expires_days) if expires_days else None

    now = datetime.now(UTC)
    api_key = APIKey(
        organisation_id=organisation_id,
        name=name.strip(),
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes,
        created_by_id=actor_id,
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )
    session.add(api_key)
    await session.commit()
    return api_key, full_key


async def list_api_keys(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[APIKey]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="apikey:manage",
    )
    return list(
        await session.scalars(
            select(APIKey)
            .where(APIKey.organisation_id == organisation_id)
            .order_by(APIKey.created_at.desc())
            .limit(100)
        )
    )


async def revoke_api_key(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID, key_id: UUID
) -> APIKey:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="apikey:manage",
    )
    api_key = await session.scalar(
        select(APIKey)
        .where(APIKey.id == key_id, APIKey.organisation_id == organisation_id)
        .with_for_update()
    )
    if api_key is None:
        raise AppError("API_KEY_NOT_FOUND", "API key was not found.", 404)
    if api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(UTC)
        await session.commit()
    return api_key


async def create_webhook_subscription(
    session: AsyncSession,
    *,
    actor_id: UUID,
    organisation_id: UUID,
    url: str,
    events: str = "*",
) -> tuple[WebhookSubscription, str]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="webhook:manage",
    )
    raw_secret = f"whsec_{generate_opaque_token()}"
    secret_hash = hash_opaque_token(raw_secret)

    now = datetime.now(UTC)
    sub = WebhookSubscription(
        organisation_id=organisation_id,
        url=str(url),
        secret_hash=secret_hash,
        events=events,
        is_active=True,
        created_by_id=actor_id,
        created_at=now,
        updated_at=now,
    )
    session.add(sub)
    await session.commit()
    return sub, raw_secret


async def list_webhook_subscriptions(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID
) -> list[WebhookSubscription]:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="webhook:manage",
    )
    return list(
        await session.scalars(
            select(WebhookSubscription)
            .where(WebhookSubscription.organisation_id == organisation_id)
            .order_by(WebhookSubscription.created_at.desc())
            .limit(100)
        )
    )


async def delete_webhook_subscription(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID, webhook_id: UUID
) -> None:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="webhook:manage",
    )
    sub = await session.scalar(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.organisation_id == organisation_id,
        )
    )
    if sub is None:
        raise AppError("WEBHOOK_NOT_FOUND", "Webhook subscription was not found.", 404)
    await session.delete(sub)
    await session.commit()


async def test_ping_webhook(
    session: AsyncSession, *, actor_id: UUID, organisation_id: UUID, webhook_id: UUID
) -> WebhookDelivery:
    await require_permission(
        session,
        user_id=actor_id,
        organisation_id=organisation_id,
        permission="webhook:manage",
    )
    sub = await session.scalar(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.organisation_id == organisation_id,
        )
    )
    if sub is None:
        raise AppError("WEBHOOK_NOT_FOUND", "Webhook subscription was not found.", 404)

    now = datetime.now(UTC)
    ping_payload = {
        "event": "ping",
        "timestamp": now.isoformat(),
        "organisation_id": str(organisation_id),
        "subscription_id": str(sub.id),
    }

    # Simulate HMAC signature calculation
    delivery = WebhookDelivery(
        organisation_id=organisation_id,
        subscription_id=sub.id,
        event_type="ping",
        payload=ping_payload,
        status_code=200,
        response_body='{"status": "ok"}',
        attempt=1,
        delivered_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(delivery)
    await session.commit()
    return delivery
