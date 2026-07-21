# Phase 3 — durable SLA workflows and real-time notifications

## Status

Complete and verified on 2026-07-16.

## Objective

Add business-time SLA targets, durable warning/breach execution, transactional delivery intents, personal notifications, and tenant-scoped real-time events without weakening the Phase 1/2 tenant and permission boundaries.

## What was delivered

- Tenant-owned business calendars with IANA timezones, weekly working intervals, and holidays.
- Category/priority SLA policies with first-response, resolution, warning, and requester-wait pause rules.
- Per-ticket SLA executions and ticket deadline fields populated atomically during ticket creation.
- Pause, resume, complete, warning, and breach SLA states.
- A Temporal workflow with durable timers plus pause, resume, and complete signals.
- A scanner/orchestrator that starts workflows idempotently and synchronises persisted SLA state into workflow signals.
- Idempotent workflow activities that record warning/breach events and enqueue delivery work.
- A transactional outbox written in the same database transaction as every ticket event.
- Claiming with `FOR UPDATE SKIP LOCKED`, exponential retry scheduling, stale-processing recovery, bounded attempts, and tenant/dedupe keys.
- In-app notifications, read state, deterministic email-provider abstraction, and delivery-attempt history.
- Redis publication and authenticated tenant-scoped WebSockets with recipient and internal-note filtering.
- Temporal, Temporal worker, SLA orchestrator, and outbox-worker Compose services.

## How it works

When a ticket is created, the ticket service finds the active policy matching its organisation, category, and priority. The calculator advances through the policy calendar in its local timezone, skipping closed intervals, weekends, and configured holidays, then stores UTC first-response and resolution deadlines. The ticket, SLA execution, immutable event, idempotency record, and outbox record commit together.

The SLA orchestrator scans persisted executions. Starting a workflow uses the stable ID `sla:{organisation_id}:{ticket_id}` with Temporal's use-existing conflict policy, so scanner retries cannot create duplicate workflows. It signals pause while the ticket waits for the requester, resume when work restarts, and complete after resolution/closure/cancellation. Temporal timers call an idempotent activity for warnings and breaches; the activity checks existing events before changing state and adding another outbox record.

The outbox worker claims due records with row locks and `SKIP LOCKED`. It creates each user's in-app notification with a unique source key, records an idempotency-keyed email delivery attempt through a provider interface, and publishes a minimal payload to the tenant's Redis channel. Failed publication marks the record failed with a bounded exponential delay; records abandoned in processing become claimable after five minutes.

WebSocket clients connect to `/api/v1/organisations/{organisation_id}/ws` and pass `Sec-WebSocket-Protocol: bearer, <access-token>`. The server validates the signed token, live authentication session, active user, and active membership before accepting. It subscribes only to `resolvehub:realtime:{organisation_id}`, filters recipient IDs, and suppresses staff-only events unless the membership has `internal_note:read`. Access tokens are not placed in URLs.

## Database migration

`20260716_0003_phase3_workflows_realtime.py` adds:

- `business_calendars` and `calendar_holidays`;
- `sla_policies` and `ticket_slas`;
- `outbox_records`, `notifications`, and `delivery_attempts`;
- SLA/outbox/delivery enum values, checks, uniqueness rules, due/claim indexes, and Phase 3 permission backfills.

The migration explicitly extends PostgreSQL's existing `sla_state` enum in an autocommit block. Its downgrade resets ticket SLA state before restoring the Phase 2 enum, drops Phase 3 enums, and removes permission mappings.

## API surface

- `POST/GET /api/v1/organisations/{organisation_id}/sla/calendars`
- `POST /api/v1/organisations/{organisation_id}/sla/calendars/{calendar_id}/holidays`
- `POST/GET /api/v1/organisations/{organisation_id}/sla/policies`
- `GET /api/v1/organisations/{organisation_id}/notifications`
- `POST /api/v1/organisations/{organisation_id}/notifications/{notification_id}/read`
- `WS /api/v1/organisations/{organisation_id}/ws`

## Security controls

- Every new persisted resource and lookup carries `organisation_id`.
- SLA configuration requires `sla:manage`; notification reads require membership, `notification:read`, tenant match, and user ownership.
- WebSockets validate current sessions and memberships rather than trusting JWT claims for permissions.
- Redis channels are tenant-specific, real-time payloads are recipient-filtered, and internal events require `internal_note:read`.
- Outbox payloads contain IDs, ticket number, event kind, recipients, and visibility only; ticket descriptions and comment bodies are excluded.
- Outbox and notification uniqueness constraints prevent duplicate user notifications during retries.
- Workflow and activity IDs are stable and tenant-qualified.

## Verification evidence

- Ruff formatting: passed for 77 files.
- Ruff lint: passed.
- Strict Mypy: passed for 73 source files.
- Unit and PostgreSQL integration/security regression suite: 27 passed in 23.97 seconds.
- Measured branch coverage: 70%; configured 70% floor passed.
- Dedicated Phase 3 integration test: passed for calendars/policies, SLA start and state changes, sensitive-payload exclusion, workflow-event deduplication, delivery retry, notification ownership, and tenant denial.
- Clean Alembic upgrade from base through all three migrations: passed.
- Alembic downgrade to base followed by clean re-upgrade: passed.
- Alembic schema-drift check: no new upgrade operations detected.
- Live Phase 2 database upgrade to Phase 3: passed after correcting existing-enum reuse.
- Docker Compose configuration: passed.
- Full local runtime launch: API, PostgreSQL, Redis, Mailpit, Temporal, Temporal worker, SLA orchestrator, and outbox worker remained running.
- API liveness returned `{"status":"ok"}`; readiness returned database and Redis as `ok`.
- Temporal `1.29.6` initialized its PostgreSQL schemas and native cluster health returned `SERVING`.
- Temporal Python SDK `1.30.0` connected to `temporal:7233`.
- A live ResolveHub worker registered workflow and activity pollers on task queue `resolvehub-sla`.

The test suite initially exposed two real integration defects: a server-generated ticket timestamp required a post-commit refresh after SLA fields changed, and ORM event IDs had to be assigned before constructing outbox dedupe keys. Both were corrected before the complete regression passed. The first live Phase 2-to-Phase 3 launch also found that generated table DDL attempted to recreate existing PostgreSQL enum types; those columns now explicitly reuse the Phase 2 types. The first local Temporal boot exceeded its startup window while performing one-time schema creation on the older Docker engine; restarting after initialization succeeded and the cluster/worker checks passed.

## Current limitations

- The included deterministic email adapter records safe delivery attempts but intentionally sends no external email. A production provider adapter and secret-managed configuration remain required.
- An authorised WebSocket's Redis subscription/filter logic is implemented, while the automated suite exercises invalid credentials and delivery payload generation rather than holding a full browser socket open.
- Temporal timer warning/breach activities are integration-tested directly and a live worker poller is verified; the suite does not wait hours for a wall-clock deadline.
- Calendars and policies currently expose create/list operations, not update/deactivate endpoints.
- First-response completion is not yet captured from the first agent response, so the stored first-response deadline is informational in this phase.
- Temporal `auto-setup` is for local development, not production deployment.

## Next milestone after verification

Phase 4: tenant-scoped PostgreSQL search and optional, replaceable AI assistance with deterministic test doubles.
