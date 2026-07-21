from resolvehub.app.core.rate_limit import _login_rate_limit_key
from resolvehub.app.modules.identity.service import authentication_failed, normalize_email


def test_email_normalization_is_stable() -> None:
    assert normalize_email("  Person@EXAMPLE.com ") == "person@example.com"


def test_login_rate_limit_key_does_not_retain_identity_data() -> None:
    identity = "127.0.0.1:person@example.com"
    key = _login_rate_limit_key(identity)
    assert "person@example.com" not in key
    assert "127.0.0.1" not in key
    assert key == _login_rate_limit_key(identity)


def test_authentication_errors_are_fresh_instances() -> None:
    first = authentication_failed()
    second = authentication_failed()
    assert first is not second
    assert first.code == second.code == "AUTHENTICATION_FAILED"
