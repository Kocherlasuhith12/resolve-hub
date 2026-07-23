# Phase 7 — RLS, storage completion, observability and production hardening

## Status

Complete. PostgreSQL Row Level Security (RLS), object-storage binary attachment upload/download, Prometheus metrics and security audit logging, production security headers and static frontend serving, demo data seeding CLI, and deployment documentation were implemented and verified on 2026-07-21.

## What has been done

- **PostgreSQL Row Level Security**: Created Alembic migration `20260721_0008_phase7_rls_storage_observability.py` enabling RLS policies across all tenant-owned tables (`memberships`, `service_categories`, `tickets`, `ticket_events`, `comments`, `attachments`, `sla_policies`, `business_calendars`, `holidays`, `notifications`, `ai_audit_logs`, `api_keys`, `webhook_subscriptions`, `webhook_deliveries`, `departments`, `idempotency_keys`, `outbox_messages`).
- **Dynamic Session Tenant Binding**: Added `set_session_organisation_id` in `resolvehub.app.core.database` setting session config `app.current_organisation_id` for database-enforced multi-tenancy.
- **Abstract Object Storage**: Implemented `StorageProvider` abstraction in `resolvehub.app.core.storage` supporting local filesystem and S3/MinIO providers with automatic stream buffering and fallback.
- **Attachment Endpoints & Domain Service**: Implemented binary file upload (`POST /api/v1/organisations/{org_id}/tickets/{ticket_id}/attachments`), listing, download stream (`GET .../download`), and deletion (`DELETE ...`) in `resolvehub.app.modules.attachments`.
- **Frontend Ticket Attachments UI**: Enhanced `TicketDetail.tsx` in the React frontend with file upload controls, file metadata badges, malware scan status indicators, binary download links, and deletion buttons.
- **Observability & Audit Logging**: Added Prometheus metrics collector (`/api/v1/metrics`) tracking HTTP request counts, latencies, active WebSockets, and security audit events. Implemented structured audit logging in `resolvehub.app.core.audit`.
- **Production Security & Static Serving**: Added security response headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`) and SPA fallback static file serving in `resolvehub.app.main`.
- **Demo Data Seeding**: Created CLI script `resolvehub.scripts.seed_demo_data` to seed Acme Corp organisation, users, departments, service categories, SLA policies, and tickets.
- **Deployment Documentation**: Created `docs/deployment.md` covering production Docker Compose setup, environment variables, RLS, MinIO S3 object storage, and monitoring.

## Verification results

Verification results on 2026-07-21:

- Backend Ruff format/lint: passed for 112 files.
- Backend Mypy strict mode: passed for 103 source files.
- Complete PostgreSQL/Redis backend regression: all 44 tests passed with 70% branch coverage.
- Frontend Oxlint: passed with 0 warnings and 0 errors across 27 files.
- Frontend TypeScript/Vite production build: passed; 90 modules transformed into production bundle.
- Frontend Vitest: all 7 component tests passed in 9.8 seconds.
- Demo Data Seeding: verified successfully via `python -m resolvehub.scripts.seed_demo_data`.

## Security behavior

- RLS policies restrict table access at the database engine level based on session setting `app.current_organisation_id`.
- Attachment uploads enforce tenant permission `attachment:create`, maximum file size limit (10MB), extension-to-MIME-type alignment, and malware scan status checks.
- Sensitive administrative and attachment operations generate structured audit log entries and Prometheus audit counters.
- Security response headers mitigate XSS, MIME-sniffing, framing, and clickjacking attacks.
