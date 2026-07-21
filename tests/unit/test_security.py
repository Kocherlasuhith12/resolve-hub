from uuid import uuid4

import jwt
import pytest

from resolvehub.app.core.config import Settings
from resolvehub.app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext_and_verifies() -> None:
    password = "correct horse battery staple"
    encoded = hash_password(password)
    assert encoded != password
    assert encoded.startswith("$argon2id$")
    assert verify_password(password, encoded)
    assert not verify_password("wrong password", encoded)


def test_opaque_tokens_are_random_and_hash_stably() -> None:
    first = generate_opaque_token()
    second = generate_opaque_token()
    assert first != second
    assert len(first) >= 64
    assert hash_opaque_token(first) == hash_opaque_token(first)
    assert first not in hash_opaque_token(first)


def test_access_token_round_trip() -> None:
    settings = Settings(jwt_secret="a" * 32)
    user_id, session_id = uuid4(), uuid4()
    token = create_access_token(user_id=user_id, session_id=session_id, settings=settings)
    assert decode_access_token(token, settings) == (user_id, session_id)


def test_access_token_rejects_wrong_secret() -> None:
    token = create_access_token(
        user_id=uuid4(), session_id=uuid4(), settings=Settings(jwt_secret="a" * 32)
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, Settings(jwt_secret="b" * 32))
