import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from resolvehub.app.core.config import get_settings
from resolvehub.app.core.database import async_session_factory
from resolvehub.app.core.security import decode_access_token
from resolvehub.app.modules.identity.models import AuthSession, User
from resolvehub.app.modules.organisations.models import Membership, Role
from resolvehub.app.modules.organisations.service import membership_has_permission

router = APIRouter(tags=["Realtime"])


def bearer_from_protocol(value: str | None) -> str | None:
    if not value:
        return None
    protocols = [item.strip() for item in value.split(",")]
    if len(protocols) == 2 and protocols[0].casefold() == "bearer" and protocols[1]:
        return protocols[1]
    return None


@router.websocket("/organisations/{organisation_id}/ws")
async def organisation_events(websocket: WebSocket, organisation_id: UUID) -> None:
    token = bearer_from_protocol(websocket.headers.get("sec-websocket-protocol"))
    if token is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required"
        )
        return
    settings = get_settings()
    try:
        user_id, session_id = decode_access_token(token, settings)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid credentials")
        return
    async with async_session_factory() as session:
        auth_session = await session.scalar(
            select(AuthSession).where(
                AuthSession.id == session_id,
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > datetime.now(UTC),
            )
        )
        user = await session.get(User, user_id)
        membership = await session.scalar(
            select(Membership)
            .options(selectinload(Membership.role).selectinload(Role.permissions))
            .where(
                Membership.organisation_id == organisation_id,
                Membership.user_id == user_id,
                Membership.is_active.is_(True),
            )
        )
    if auth_session is None or user is None or not user.is_active or membership is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
        return
    can_read_internal = membership_has_permission(membership, "internal_note:read")
    await websocket.accept(subprotocol="bearer")
    redis = Redis.from_url(settings.redis_url)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"resolvehub:realtime:{organisation_id}")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.05)
                continue
            raw = message["data"]
            payload = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            recipients = payload.get("recipient_ids", [])
            if recipients and str(user_id) not in recipients:
                continue
            if payload.get("visibility") == "staff" and not can_read_internal:
                continue
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await redis.aclose()
