import pytest
from pydantic import ValidationError

from resolvehub.app.core.config import Settings


def test_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret="short")


def test_requires_secure_browser_cookie_outside_local_and_test() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", browser_cookie_secure=False)

    settings = Settings(environment="production", browser_cookie_secure=True)
    assert settings.browser_cookie_secure is True
