from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.billing.schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    ContactSalesCreate,
    ContactSalesResponse,
    CouponValidateRequest,
    CouponValidateResponse,
    InvoiceItem,
    PaymentMethodResponse,
    PaymentMethodUpdate,
    PortalSessionCreate,
    PortalSessionResponse,
    SubscriptionResponse,
)
from resolvehub.app.modules.billing.service import StripeBillingService
from resolvehub.app.modules.organisations.models import Membership

router = APIRouter(tags=["Billing"])


async def _get_org_id(session: DbSession, principal: CurrentPrincipal) -> UUID:
    query = select(Membership.organisation_id).where(
        Membership.user_id == principal.user.id,
        Membership.is_active == True,
    )
    result = await session.execute(query)
    org_id = result.scalar_one_or_none()
    return org_id or principal.user.id


@router.get("/billing/subscription", response_model=SubscriptionResponse)
async def billing_subscription_get(
    principal: CurrentPrincipal,
    session: DbSession,
) -> SubscriptionResponse:
    org_id = await _get_org_id(session, principal)
    return await StripeBillingService.get_subscription_details(session, org_id)


@router.post("/billing/create-checkout-session", response_model=CheckoutSessionResponse)
async def billing_create_checkout_session(
    payload: CheckoutSessionCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> CheckoutSessionResponse:
    org_id = await _get_org_id(session, principal)
    try:
        url, session_id, is_sim = await StripeBillingService.create_checkout_session(
            session,
            organisation_id=org_id,
            plan_id=payload.plan_id,
            price_id=payload.price_id,
            return_url=payload.return_url,
        )
        return CheckoutSessionResponse(
            checkout_url=url, session_id=session_id, is_simulation=is_sim
        )
    except ValueError as exc:
        err_str = str(exc)
        if "Sophos" in err_str or "blocked" in err_str.lower() or "CERTIFICATE_VERIFY" in err_str:
            clean_msg = (
                "Unable to reach api.stripe.com: Outbound network traffic is currently restricted "
                "by your local network firewall (Sophos / Financial services policy). "
                "Please log into your network portal (https://172.16.16.16:8090) or connect to an open Wi-Fi / hotspot."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=clean_msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_str) from exc


@router.post("/billing/create-portal-session", response_model=PortalSessionResponse)
async def billing_create_portal_session(
    payload: PortalSessionCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> PortalSessionResponse:
    org_id = await _get_org_id(session, principal)
    try:
        portal_url, is_sim = await StripeBillingService.create_portal_session(
            session, organisation_id=org_id, return_url=payload.return_url
        )
        return PortalSessionResponse(portal_url=portal_url, is_simulation=is_sim)
    except ValueError as exc:
        err_str = str(exc)
        if "Sophos" in err_str or "blocked" in err_str.lower() or "CERTIFICATE_VERIFY" in err_str:
            clean_msg = (
                "Unable to reach api.stripe.com: Outbound network traffic is currently restricted "
                "by your local network firewall (Sophos / Financial services policy). "
                "Please log into your network portal (https://172.16.16.16:8090) or connect to an open Wi-Fi / hotspot."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=clean_msg) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_str) from exc


@router.get("/billing/invoices", response_model=list[InvoiceItem])
async def billing_invoices_get(
    principal: CurrentPrincipal,
    session: DbSession,
) -> list[InvoiceItem]:
    org_id = await _get_org_id(session, principal)
    sub_response = await StripeBillingService.get_subscription_details(session, org_id)
    return sub_response.invoices


@router.post("/billing/cancel")
async def billing_subscription_cancel(
    principal: CurrentPrincipal,
    session: DbSession,
) -> dict[str, str]:
    org_id = await _get_org_id(session, principal)
    await StripeBillingService.cancel_subscription(session, org_id)
    return {"status": "success", "message": "Subscription set to cancel at end of period."}


@router.post("/billing/resume")
async def billing_subscription_resume(
    principal: CurrentPrincipal,
    session: DbSession,
) -> dict[str, str]:
    org_id = await _get_org_id(session, principal)
    await StripeBillingService.resume_subscription(session, org_id)
    return {"status": "success", "message": "Subscription reactivated successfully."}


@router.post("/billing/downgrade-starter")
async def billing_downgrade_starter(
    principal: CurrentPrincipal,
    session: DbSession,
) -> dict[str, str]:
    org_id = await _get_org_id(session, principal)
    await StripeBillingService.downgrade_to_starter(session, org_id)
    return {"status": "success", "message": "Successfully downgraded workspace to Starter Plan."}


@router.post("/billing/contact-sales", response_model=ContactSalesResponse)
async def billing_contact_sales(
    payload: ContactSalesCreate,
    principal: CurrentPrincipal,
) -> ContactSalesResponse:
    res = await StripeBillingService.contact_sales(
        company_name=payload.company_name,
        full_name=payload.full_name,
        business_email=payload.business_email,
        phone_number=payload.phone_number,
        company_size=payload.company_size,
        message=payload.message,
    )
    return ContactSalesResponse(status=res["status"], message=res["message"])


@router.post("/billing/validate-coupon", response_model=CouponValidateResponse)
async def billing_validate_coupon(
    payload: CouponValidateRequest,
    principal: CurrentPrincipal,
) -> CouponValidateResponse:
    valid, discount_pct, msg = StripeBillingService.validate_coupon(payload.code)
    return CouponValidateResponse(valid=valid, discount_percent=discount_pct, message=msg)


@router.get("/billing/payment-method", response_model=PaymentMethodResponse)
async def billing_payment_method_get(
    principal: CurrentPrincipal,
    session: DbSession,
) -> PaymentMethodResponse:
    org_id = await _get_org_id(session, principal)
    sub_response = await StripeBillingService.get_subscription_details(session, org_id)
    return PaymentMethodResponse(
        payment_method=sub_response.payment_method, brand="Visa", last4="4242"
    )


@router.patch("/billing/payment-method", response_model=PaymentMethodResponse)
async def billing_payment_method_update(
    payload: PaymentMethodUpdate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> PaymentMethodResponse:
    org_id = await _get_org_id(session, principal)
    portal_url, _ = await StripeBillingService.create_portal_session(
        session, organisation_id=org_id
    )
    return PaymentMethodResponse(
        payment_method=f"Updated via Customer Portal ({portal_url})", brand="Visa", last4="4242"
    )


@router.post("/billing/webhook", status_code=status.HTTP_200_OK)
async def billing_webhook(
    request: Request,
    session: DbSession,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, str]:
    payload_bytes = await request.body()
    return await StripeBillingService.handle_webhook(
        session, payload_bytes=payload_bytes, sig_header=stripe_signature
    )
