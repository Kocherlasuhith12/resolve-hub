from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutSessionCreate(BaseModel):
    price_id: str | None = None
    plan_id: str | None = None
    return_url: str | None = None


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    is_simulation: bool = False


class PortalSessionCreate(BaseModel):
    return_url: str | None = None


class PortalSessionResponse(BaseModel):
    portal_url: str
    is_simulation: bool = False


class PaymentMethodUpdate(BaseModel):
    payment_method_id: str


class PaymentMethodResponse(BaseModel):
    payment_method: str
    brand: str | None = None
    last4: str | None = None


class PlanFeature(BaseModel):
    name: str
    included: bool


class PlanTier(BaseModel):
    id: str
    name: str
    price_monthly: int
    price_yearly: int
    description: str
    is_current: bool
    features: list[PlanFeature]


class UsageMeter(BaseModel):
    name: str
    used: float
    limit: int
    unit: str


class InvoiceItem(BaseModel):
    id: str
    invoice_number: str
    date: datetime
    amount: float
    status: str
    pdf_url: str


class SubscriptionResponse(BaseModel):
    plan_name: str
    status: str
    billing_cycle: str
    next_billing_date: datetime
    payment_method: str
    usage: list[UsageMeter]
    available_plans: list[PlanTier]
    invoices: list[InvoiceItem]
    cancel_at_period_end: bool = False


class ContactSalesCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    full_name: str = Field(..., min_length=2, max_length=120)
    business_email: str = Field(..., min_length=5, max_length=120)
    phone_number: str | None = Field(None, max_length=40)
    company_size: str = Field("10-50", max_length=40)
    message: str = Field("", max_length=2000)


class ContactSalesResponse(BaseModel):
    status: str
    message: str


class CouponValidateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)


class CouponValidateResponse(BaseModel):
    valid: bool
    discount_percent: float
    message: str
