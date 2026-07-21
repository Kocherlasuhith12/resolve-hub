import base64
import json
from datetime import datetime
from uuid import UUID

from resolvehub.app.core.exceptions import AppError


def encode_cursor(created_at: datetime, item_id: UUID) -> str:
    payload = json.dumps({"created_at": created_at.isoformat(), "id": str(item_id)}).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        return datetime.fromisoformat(payload["created_at"]), UUID(payload["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise AppError("PAGINATION_CURSOR_INVALID", "Pagination cursor is invalid.", 400) from None
