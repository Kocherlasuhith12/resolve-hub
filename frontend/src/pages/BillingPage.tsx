import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { CreditCard, Zap, Check, Download, Building, Loader2, X, Send } from 'lucide-react'
import { useAuth } from '../auth/useAuth'

type PlanFeature = {
  name: string
  included: boolean
}

type PlanTier = {
  id: string
  name: string
  price_monthly: number
  price_yearly: number
  description: string
  is_current: boolean
  features: PlanFeature[]
}

type UsageMeter = {
  name: string
  used: number
  limit: number
  unit: string
}

type InvoiceItem = {
  id: string
  invoice_number: string
  date: string
  amount: number
  status: string
  pdf_url: string
}

type SubscriptionResponse = {
  plan_name: string
  status: string
  billing_cycle: string
  next_billing_date: string
  payment_method: string
  usage: UsageMeter[]
  available_plans: PlanTier[]
  invoices: InvoiceItem[]
  cancel_at_period_end?: boolean
}

type CheckoutResponse = {
  checkout_url: string
  session_id: string
  is_simulation?: boolean
}

type PortalResponse = {
  portal_url: string
  is_simulation?: boolean
}

type CouponResponse = {
  valid: boolean
  discount_percent: number
  message: string
}

export function BillingPage() {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [couponCode, setCouponCode] = useState('')
  const [couponInfo, setCouponInfo] = useState<{ discount: number; msg: string } | null>(null)

  // Sales Contact Modal state
  const [isSalesModalOpen, setIsSalesModalOpen] = useState(false)
  const [salesForm, setSalesForm] = useState({
    companyName: 'Acme Corp',
    fullName: 'Acme Admin',
    businessEmail: 'admin@acme.example.com',
    phoneNumber: '',
    companySize: '50-200',
    message: 'Interested in dedicated enterprise infrastructure with custom SLA.',
  })

  useEffect(() => {
    if (searchParams.get('success') === 'true') {
      setSuccessMsg('🎉 Subscription checkout completed successfully!')
      searchParams.delete('success')
      searchParams.delete('session_id')
      setSearchParams(searchParams, { replace: true })
      setTimeout(() => setSuccessMsg(null), 6000)
    } else if (searchParams.get('cancelled') === 'true') {
      setSuccessMsg('Checkout was cancelled. No charges were made.')
      searchParams.delete('cancelled')
      setSearchParams(searchParams, { replace: true })
      setTimeout(() => setSuccessMsg(null), 5000)
    }
  }, [searchParams, setSearchParams])

  const subscriptionQuery = useQuery({
    queryKey: ['billing-subscription'],
    queryFn: () => request<SubscriptionResponse>('/billing/subscription'),
  })

  const checkoutMutation = useMutation({
    mutationFn: (planId: string) =>
      request<CheckoutResponse>('/billing/create-checkout-session', {
        method: 'POST',
        body: JSON.stringify({
          plan_id: planId,
          return_url: `${window.location.origin}/settings/billing`,
        }),
      }),
    onSuccess: (data) => {
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      }
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to initiate Stripe Checkout.')
      setTimeout(() => setErrorMsg(null), 5000)
    },
  })

  const portalMutation = useMutation({
    mutationFn: () =>
      request<PortalResponse>('/billing/create-portal-session', {
        method: 'POST',
        body: JSON.stringify({
          return_url: `${window.location.origin}/settings/billing`,
        }),
      }),
    onSuccess: (data) => {
      if (data.is_simulation) {
        setSuccessMsg(
          '💳 Card Update & Subscription Portal (Simulation Mode): In local development without live Stripe keys, payment method updates are simulated. To open live Stripe Billing Portal, add your live sk_test_... secret key in .env.'
        )
        setTimeout(() => setSuccessMsg(null), 8000)
      } else if (data.portal_url) {
        window.location.href = data.portal_url
      }
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to open Stripe Customer Portal.')
      setTimeout(() => setErrorMsg(null), 5000)
    },
  })

  const downgradeMutation = useMutation({
    mutationFn: () =>
      request<{ status: string; message: string }>('/billing/downgrade-starter', {
        method: 'POST',
      }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['billing-subscription'] })
      setSuccessMsg(data.message || 'Workspace downgraded to Starter Plan.')
      setTimeout(() => setSuccessMsg(null), 5000)
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to downgrade plan.')
      setTimeout(() => setErrorMsg(null), 5000)
    },
  })

  const couponMutation = useMutation({
    mutationFn: (code: string) =>
      request<CouponResponse>('/billing/validate-coupon', {
        method: 'POST',
        body: JSON.stringify({ code }),
      }),
    onSuccess: (data) => {
      if (data.valid) {
        setCouponInfo({ discount: data.discount_percent, msg: data.message })
        setSuccessMsg(data.message)
        setErrorMsg(null)
      } else {
        setCouponInfo(null)
        setErrorMsg(data.message)
      }
    },
  })

  const contactSalesMutation = useMutation({
    mutationFn: () =>
      request<{ status: string; message: string }>('/billing/contact-sales', {
        method: 'POST',
        body: JSON.stringify({
          company_name: salesForm.companyName,
          full_name: salesForm.fullName,
          business_email: salesForm.businessEmail,
          phone_number: salesForm.phoneNumber || null,
          company_size: salesForm.companySize,
          message: salesForm.message,
        }),
      }),
    onSuccess: (data) => {
      setIsSalesModalOpen(false)
      setSuccessMsg(data.message)
      setTimeout(() => setSuccessMsg(null), 6000)
    },
  })

  const subscription = subscriptionQuery.data

  const plans = subscription?.available_plans ?? [
    {
      id: 'starter',
      name: 'Starter Plan',
      price_monthly: 0,
      price_yearly: 0,
      description: 'Essential ticketing & issue tracking for small teams',
      is_current: false,
      features: [
        { name: 'Up to 5 team members', included: true },
        { name: '1 GB File Storage', included: true },
        { name: 'Standard Email Support', included: true },
        { name: 'Basic Incident Triage', included: true },
      ],
    },
    {
      id: 'pro',
      name: 'Professional Enterprise',
      price_monthly: 49,
      price_yearly: 490,
      description: 'Complete operational platform with AI copilot & SLA workflows',
      is_current: true,
      features: [
        { name: 'Unlimited Team Members', included: true },
        { name: '100 GB High-Speed Storage', included: true },
        { name: '24/7 Priority SLA Monitoring', included: true },
        { name: 'AI Copilot & Smart Categorization', included: true },
        { name: 'Custom Webhooks & Integrations', included: true },
        { name: 'Exportable Audit Logs', included: true },
      ],
    },
    {
      id: 'enterprise',
      name: 'Enterprise Dedicated',
      price_monthly: 199,
      price_yearly: 1990,
      description: 'Single-tenant isolated deployment with custom SLA & support',
      is_current: false,
      features: [
        { name: 'Dedicated AWS Region / VPC', included: true },
        { name: 'Unlimited Storage & Custom Log Retention', included: true },
        { name: 'Dedicated Technical Account Manager', included: true },
        { name: 'Custom AI Model Fine-tuning', included: true },
        { name: 'SAML 2.0 / Okta Single Sign-On', included: true },
      ],
    },
  ]

  const usageMeters = subscription?.usage ?? [
    { name: 'Active Team Members', used: 8, limit: 50, unit: 'seats' },
    { name: 'Cloud File Storage', used: 24.5, limit: 100, unit: 'GB' },
    { name: 'Monthly API Requests', used: 14200, limit: 100000, unit: 'calls' },
    { name: 'AI Copilot Queries', used: 320, limit: 2000, unit: 'queries' },
  ]

  const invoices = subscription?.invoices ?? [
    { id: 'inv-1', invoice_number: 'INV-2026-007', date: new Date().toISOString(), amount: 49.0, status: 'PAID', pdf_url: '#' },
    { id: 'inv-2', invoice_number: 'INV-2026-006', date: new Date().toISOString(), amount: 49.0, status: 'PAID', pdf_url: '#' },
  ]

  function handlePlanAction(planId: string, isCurrent: boolean) {
    if (isCurrent) {
      portalMutation.mutate()
      return
    }
    if (planId === 'enterprise') {
      setIsSalesModalOpen(true)
      return
    }
    if (planId === 'starter') {
      if (window.confirm('Are you sure you want to downgrade to the Starter Plan?')) {
        downgradeMutation.mutate()
      }
      return
    }
    checkoutMutation.mutate(planId)
  }

  function handleApplyCoupon() {
    if (couponCode.trim()) {
      couponMutation.mutate(couponCode.trim())
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Billing & Subscription</h1>
        <p className="page-subtitle">Manage plan tiers, active usage meters, billing contact details, and invoice history</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div className="form-error" role="alert" style={{ marginBottom: 20 }}>
          {errorMsg}
        </div>
      )}

      {/* Usage Gauges */}
      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-header">
          <h3><Zap size={18} style={{ display: 'inline', marginRight: 6 }} /> Monthly Usage Meters</h3>
        </div>
        <div className="kpi-grid" style={{ marginTop: 12 }}>
          {usageMeters.map((meter) => {
            const pct = Math.round((meter.used / meter.limit) * 100)
            return (
              <div key={meter.name} className="kpi-card">
                <div className="kpi-header">
                  <span className="kpi-title">{meter.name}</span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#16a34a' }}>{pct}% used</span>
                </div>
                <div className="kpi-value" style={{ fontSize: '1.2rem', marginTop: 4 }}>
                  {meter.used} / {meter.limit} <span style={{ fontSize: '0.8rem', fontWeight: 'normal' }}>{meter.unit}</span>
                </div>
                <div style={{ height: 6, width: '100%', background: '#e2e8f0', borderRadius: 3, marginTop: 8, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: '#16a34a', borderRadius: 3 }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Subscription Plans */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 24 }}>
        {plans.map((plan) => {
          let priceDisplay = plan.id === 'enterprise' ? 'Custom' : `$${plan.price_monthly}`
          if (couponInfo && plan.price_monthly > 0 && !plan.is_current) {
            const discountedPrice = Math.round(plan.price_monthly * (1 - couponInfo.discount / 100))
            priceDisplay = `$${discountedPrice}`
          }

          return (
            <div
              key={plan.id}
              className="panel"
              style={{
                border: plan.is_current ? '2px solid #16A34A' : '1px solid #e2e8f0',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              {plan.is_current && (
                <span
                  style={{
                    position: 'absolute',
                    top: -12,
                    right: 16,
                    background: '#16A34A',
                    color: '#ffffff',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '2px 10px',
                    borderRadius: 12,
                    textTransform: 'uppercase',
                  }}
                >
                  Current Plan
                </span>
              )}
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: 4 }}>{plan.name}</h3>
                <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 12 }}>{plan.description}</p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 16 }}>
                  <span style={{ fontSize: '2rem', fontWeight: 700 }}>{priceDisplay}</span>
                  <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                    {plan.id === 'enterprise' ? '' : 'per month'}
                  </span>
                  {couponInfo && plan.price_monthly > 0 && !plan.is_current && (
                    <span style={{ fontSize: '0.75rem', color: '#16a34a', fontWeight: 600, marginLeft: 6 }}>
                      ({couponInfo.discount}% OFF applied)
                    </span>
                  )}
                </div>

                <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.85rem' }}>
                  {plan.features.map((feat) => (
                    <li key={feat.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#334155' }}>
                      <Check size={14} style={{ color: feat.included ? '#16a34a' : '#94a3b8', flexShrink: 0 }} />
                      {feat.name}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                type="button"
                className={plan.is_current ? 'btn-secondary' : 'btn-primary'}
                style={{ marginTop: 20, width: '100%' }}
                disabled={checkoutMutation.isPending || portalMutation.isPending || downgradeMutation.isPending}
                onClick={() => handlePlanAction(plan.id, plan.is_current)}
              >
                {checkoutMutation.isPending || portalMutation.isPending || downgradeMutation.isPending ? (
                  <>
                    <Loader2 size={14} className="loading-spinner" style={{ display: 'inline', marginRight: 6 }} /> Processing…
                  </>
                ) : plan.is_current ? (
                  'Manage Subscription'
                ) : plan.id === 'enterprise' ? (
                  'Contact Sales'
                ) : plan.id === 'starter' ? (
                  'Downgrade to Starter'
                ) : (
                  `Upgrade to ${plan.name}`
                )}
              </button>
            </div>
          )
        })}
      </div>

      <div className="dashboard-panels">
        {/* Payment Method & Coupons */}
        <div className="panel">
          <div className="panel-header">
            <h3><CreditCard size={18} style={{ display: 'inline', marginRight: 6 }} /> Payment Method & Promotion</h3>
          </div>
          <div className="compact-form">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, border: '1px solid #e2e8f0', borderRadius: 8, background: '#f8fafc' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <CreditCard size={24} style={{ color: '#2563eb' }} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{subscription?.payment_method ?? 'Visa ending in 4242'}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Expires 12/2028 • Default payment method</div>
                </div>
              </div>
              <button
                className="btn-secondary"
                type="button"
                style={{ fontSize: '0.8rem', padding: '4px 10px' }}
                disabled={portalMutation.isPending}
                onClick={() => portalMutation.mutate()}
              >
                {portalMutation.isPending ? 'Opening…' : 'Update Card'}
              </button>
            </div>

            <label style={{ marginTop: 12 }}>
              <span>Promotional Coupon Code</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  placeholder="e.g. RESOLVE20"
                />
                <button
                  className="btn-secondary"
                  type="button"
                  disabled={couponMutation.isPending}
                  onClick={handleApplyCoupon}
                >
                  {couponMutation.isPending ? 'Validating…' : 'Apply'}
                </button>
              </div>
            </label>
          </div>
        </div>

        {/* Invoice History */}
        <div className="panel">
          <div className="panel-header">
            <h3><Building size={18} style={{ display: 'inline', marginRight: 6 }} /> Invoice History</h3>
          </div>
          <table className="tickets-table" style={{ marginTop: 8 }}>
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td style={{ fontWeight: 600 }}>{inv.invoice_number}</td>
                  <td>
                    <time dateTime={inv.date}>
                      {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(inv.date))}
                    </time>
                  </td>
                  <td>${inv.amount.toFixed(2)}</td>
                  <td><span className="badge badge-success">{inv.status}</span></td>
                  <td>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                      onClick={() => {
                        if (inv.pdf_url && inv.pdf_url !== '#') {
                          window.open(inv.pdf_url, '_blank')
                        } else {
                          alert(`Downloading invoice receipt ${inv.invoice_number}`)
                        }
                      }}
                    >
                      <Download size={12} style={{ display: 'inline', marginRight: 4 }} /> PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enterprise Contact Sales Modal */}
      {isSalesModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: 520,
              width: '100%',
              background: '#ffffff',
              borderRadius: 12,
              padding: 24,
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>Contact Enterprise Sales</h2>
              <button
                type="button"
                className="btn-icon"
                onClick={() => setIsSalesModalOpen(false)}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>
            <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: 20 }}>
              Speak with our solution engineering team for dedicated infrastructure, SAML SSO, and custom SLA agreements.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault()
                contactSalesMutation.mutate()
              }}
              style={{ display: 'flex', flexDirection: 'column', gap: 14 }}
            >
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <label>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Company Name *</span>
                  <input
                    required
                    value={salesForm.companyName}
                    onChange={(e) => setSalesForm({ ...salesForm, companyName: e.target.value })}
                  />
                </label>
                <label>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Full Name *</span>
                  <input
                    required
                    value={salesForm.fullName}
                    onChange={(e) => setSalesForm({ ...salesForm, fullName: e.target.value })}
                  />
                </label>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <label>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Business Email *</span>
                  <input
                    type="email"
                    required
                    value={salesForm.businessEmail}
                    onChange={(e) => setSalesForm({ ...salesForm, businessEmail: e.target.value })}
                  />
                </label>
                <label>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Phone Number</span>
                  <input
                    type="tel"
                    value={salesForm.phoneNumber}
                    placeholder="+1 (555) 000-0000"
                    onChange={(e) => setSalesForm({ ...salesForm, phoneNumber: e.target.value })}
                  />
                </label>
              </div>

              <label>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Company Size</span>
                <select
                  value={salesForm.companySize}
                  onChange={(e) => setSalesForm({ ...salesForm, companySize: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1' }}
                >
                  <option value="1-10">1 - 10 employees</option>
                  <option value="10-50">10 - 50 employees</option>
                  <option value="50-200">50 - 200 employees</option>
                  <option value="200-1000">200 - 1,000 employees</option>
                  <option value="1000+">1,000+ employees</option>
                </select>
              </label>

              <label>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>Requirements & Notes</span>
                <textarea
                  rows={3}
                  value={salesForm.message}
                  onChange={(e) => setSalesForm({ ...salesForm, message: e.target.value })}
                />
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setIsSalesModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={contactSalesMutation.isPending}
                >
                  {contactSalesMutation.isPending ? (
                    <>
                      <Loader2 size={14} className="loading-spinner" style={{ display: 'inline', marginRight: 6 }} /> Submitting…
                    </>
                  ) : (
                    <>
                      <Send size={14} style={{ display: 'inline', marginRight: 6 }} /> Submit Sales Request
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
