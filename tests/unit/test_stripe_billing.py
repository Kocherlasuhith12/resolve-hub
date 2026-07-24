from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from resolvehub.app.modules.billing.models import Subscription
from resolvehub.app.modules.billing.service import StripeBillingService


@pytest.mark.asyncio
async def test_get_or_create_subscription_record() -> None:
    org_id = uuid4()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    sub = await StripeBillingService.get_or_create_subscription_record(mock_session, org_id)
    assert sub.organisation_id == org_id
    assert sub.plan_name == "Professional Enterprise"
    assert sub.status == "active"
    assert sub.cancel_at_period_end is False


@pytest.mark.asyncio
async def test_get_subscription_details() -> None:
    org_id = uuid4()
    mock_session = AsyncMock()
    existing_sub = Subscription(
        organisation_id=org_id,
        plan_name="Professional Enterprise",
        status="active",
        cancel_at_period_end=False,
    )
    mock_result1 = MagicMock()
    mock_result1.scalar_one_or_none.return_value = existing_sub

    mock_result2 = MagicMock()
    mock_result2.scalars.return_value.all.return_value = []

    mock_session.execute.side_effect = [mock_result1, mock_result2]

    sub_response = await StripeBillingService.get_subscription_details(mock_session, org_id)
    assert sub_response.plan_name == "Professional Enterprise"
    assert len(sub_response.available_plans) == 3
    assert len(sub_response.usage) == 4
    assert len(sub_response.invoices) >= 1


@pytest.mark.asyncio
async def test_cancel_and_resume_subscription() -> None:
    org_id = uuid4()
    mock_session = AsyncMock()
    existing_sub = Subscription(
        organisation_id=org_id,
        plan_name="Professional Enterprise",
        status="active",
        cancel_at_period_end=False,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_session.execute.return_value = mock_result

    sub_cancelled = await StripeBillingService.cancel_subscription(mock_session, org_id)
    assert sub_cancelled.cancel_at_period_end is True

    sub_resumed = await StripeBillingService.resume_subscription(mock_session, org_id)
    assert sub_resumed.cancel_at_period_end is False


@pytest.mark.asyncio
@patch("stripe.checkout.Session.create")
async def test_create_checkout_session(mock_checkout_create: MagicMock) -> None:
    mock_session_obj = MagicMock()
    mock_session_obj.url = "https://checkout.stripe.com/pay/cs_test_123"
    mock_session_obj.id = "cs_test_123"
    mock_checkout_create.return_value = mock_session_obj

    org_id = uuid4()
    mock_session = AsyncMock()
    existing_sub = Subscription(
        organisation_id=org_id,
        stripe_customer_id="cus_test_123",
        plan_name="Professional Enterprise",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_session.execute.return_value = mock_result

    url, session_id, is_sim = await StripeBillingService.create_checkout_session(
        mock_session, organisation_id=org_id, plan_id="pro"
    )
    assert "cs_test_" in session_id


@pytest.mark.asyncio
@patch("stripe.billing_portal.Session.create")
async def test_create_portal_session(mock_portal_create: MagicMock) -> None:
    mock_portal_obj = MagicMock()
    mock_portal_obj.url = "https://billing.stripe.com/session/test_123"
    mock_portal_create.return_value = mock_portal_obj

    org_id = uuid4()
    mock_session = AsyncMock()
    existing_sub = Subscription(
        organisation_id=org_id,
        stripe_customer_id="cus_test_123",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_session.execute.return_value = mock_result

    url, is_sim = await StripeBillingService.create_portal_session(
        mock_session, organisation_id=org_id
    )
    assert "billing" in url


@pytest.mark.asyncio
async def test_webhook_handler_unauthenticated() -> None:
    mock_session = AsyncMock()
    res = await StripeBillingService.handle_webhook(mock_session, b"{}", None)
    assert res["status"] in ("received", "error", "success")


@pytest.mark.asyncio
async def test_downgrade_to_starter() -> None:
    org_id = uuid4()
    mock_session = AsyncMock()
    existing_sub = Subscription(
        organisation_id=org_id,
        plan_name="Professional Enterprise",
        status="active",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_sub
    mock_session.execute.return_value = mock_result

    sub = await StripeBillingService.downgrade_to_starter(mock_session, org_id)
    assert sub.plan_name == "Starter Plan"


@pytest.mark.asyncio
async def test_contact_sales() -> None:
    res = await StripeBillingService.contact_sales(
        company_name="Acme",
        full_name="Alice Admin",
        business_email="alice@acme.example.com",
        phone_number=None,
        company_size="50-200",
        message="Enterprise inquiry",
    )
    assert res["status"] == "success"


def test_validate_coupon() -> None:
    valid, pct, msg = StripeBillingService.validate_coupon("RESOLVE20")
    assert valid is True
    assert pct == 20.0

    invalid, pct2, msg2 = StripeBillingService.validate_coupon("INVALID_CODE_99")
    assert invalid is False
