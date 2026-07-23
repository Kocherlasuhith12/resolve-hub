# Phase 6 — administration lifecycle, analytics and integrations

## Status

Complete. Full administration lifecycle, member role and status management, service category and SLA policy editing, tenant-scoped analytics metrics and CSV export, hashed developer API keys, HMAC-SHA256 signed webhook subscriptions and test ping delivery were implemented and verified on 2026-07-21.

## What has been done

- Added member role updates (`PATCH /api/v1/organisations/{org_id}/members/{membership_id}/role`) and status toggles (`PATCH /api/v1/organisations/{org_id}/members/{membership_id}/status`) with safety checks preventing deactivation or demotion of the last active Organisation Admin.
- Added service category lifecycle update (`PATCH /api/v1/organisations/{org_id}/categories/{category_id}`) for editing category name, default priority, and active state.
- Added SLA policy lifecycle update (`PATCH /api/v1/organisations/{org_id}/sla/policies/{policy_id}`) for editing first-response/resolution targets, warning percentages, and active state.
- Added tenant-scoped analytics summary (`GET /api/v1/organisations/{org_id}/analytics/summary`) providing ticket counts by status, priority, category, SLA breach counts, and SLA compliance percentage.
- Added streaming operational CSV ticket export (`GET /api/v1/organisations/{org_id}/analytics/exports/tickets`).
- Added developer API key management (`POST /api/v1/organisations/{org_id}/api-keys`, `GET`, `DELETE`) with prefix generation, SHA-256 hashed token storage, and single-time secret key disclosure.
- Added HMAC-signed Webhook subscriptions (`POST /api/v1/organisations/{org_id}/webhooks`, `GET`, `DELETE`, `POST .../test`) with ping test delivery logging.
- Created Alembic database migration `20260721_0007_phase6_lifecycle_analytics_integrations.py` creating `api_keys`, `webhook_subscriptions`, and `webhook_deliveries` tables.
- Enhanced frontend Administration Workspace with tabs for Lifecycle & Controls, Analytics & Reports (with CSV export button), and Developer Settings.

## How it works

The selected organisation ID scopes every request. FastApi route dependencies authenticate the principal and domain services validate permission strings (`member:update`, `category:update`, `sla:manage`, `analytics:read`, `apikey:manage`, `webhook:manage`).

API key creation generates a random opaque token, returns full key `rh_<prefix>_<token>` once, and stores only its SHA-256 hash. Webhook subscriptions generate an HMAC secret and allow triggering test pings that record delivery attempts with status codes and response payloads.

The React administration workspace provides sub-tabs for administrative lifecycle tasks, visual analytics summary metrics with download link, and developer API key / Webhook controls.

## Is it working?

Yes.

Verification results on 2026-07-21:

- Backend Ruff format/lint: passed for 105 files.
- Backend Mypy strict mode: passed for 97 source files.
- Complete PostgreSQL/Redis backend regression: all 44 tests passed in 57 seconds with 70% branch coverage.
- Frontend Oxlint: passed with 0 warnings and 0 errors across 27 files.
- Frontend TypeScript/Vite production build: passed; 90 modules transformed into production bundle.
- Frontend Vitest: all 7 component tests passed in 10.18 seconds.
- Playwright E2E browser tests: passed on desktop and mobile Chromium.

## Security behavior

- Every operation is tenant-scoped by `organisation_id` and permission-checked in route and service layers.
- API Key and Webhook secrets are hashed (`SHA-256`) before database persistence and never logged.
- Admin deactivation/demotion is guarded against leaving an organisation with zero active administrators.
- Webhook ping payloads include ISO UTC timestamps and HMAC signature context.
- Exports and analytics strictly enforce `analytics:read` tenant authorization.
