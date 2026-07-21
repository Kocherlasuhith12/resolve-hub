from datetime import UTC, datetime
from uuid import uuid4

import pytest

from resolvehub.app.core.exceptions import AppError
from resolvehub.app.core.pagination import decode_cursor, encode_cursor
from resolvehub.app.modules.tickets.service import request_fingerprint


def test_cursor_round_trip() -> None:
    created_at, item_id = datetime.now(UTC), uuid4()
    assert decode_cursor(encode_cursor(created_at, item_id)) == (created_at, item_id)


def test_invalid_cursor_has_domain_error() -> None:
    with pytest.raises(AppError) as error:
        decode_cursor("not-a-cursor")
    assert error.value.code == "PAGINATION_CURSOR_INVALID"


def test_request_fingerprint_is_order_independent() -> None:
    assert request_fingerprint({"a": 1, "b": 2}) == request_fingerprint({"b": 2, "a": 1})
