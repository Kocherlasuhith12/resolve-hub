# Delivery roadmap

## Phase 0 — discovery and design (complete)

The repository was empty and not initialized as Git. This document, the architecture overview, permanent rules, and the first milestone define the initial direction.

## Phase 1 — foundation and identity (complete)

Build and verify configuration, PostgreSQL/Alembic, Redis, logging and errors, authentication with rotating sessions, organisations, invitations, memberships, permission roles, departments, tenant tests, Docker Compose, and CI.

## Phase 2 — core ticket operations (complete)

Service categories, tenant-isolated ticket creation and filtering, assignment, explicit state transitions, public comments, private notes, immutable events, optimistic concurrency, idempotent creation, attachment metadata, and cursor pagination.

## Phase 3 — durable workflows and notifications (complete)

Temporal-backed SLA warnings/breaches, business calendars, transactional outbox notifications, WebSockets, and Redis distribution.

## Phase 4 — search and optional AI assistance (complete)

PostgreSQL full-text ticket search, advanced filters, optional semantic similarity, replaceable AI suggestion providers, deterministic fakes, AI audit records, confidence, and human approval.

## Phase 5 — responsive end-user frontend (complete)

Built and verified a responsive TypeScript application for requesters, agents, and administrators. It includes secure rotating browser sessions with coordinated 401 recovery, permission-aware navigation, registration/local verification, organisation/catalogue setup, requester ticket workflows, agent queues and eligible-agent assignment, supported administration creation, personal notifications, authenticated real-time refresh, and manual AI suggestion review. Complete backend, component, deterministic browser, and live desktop/mobile gates passed on 2026-07-20.

## Phase 6 — administration lifecycle, analytics and integrations (in progress)

The first checkpoint is complete: tenant-scoped member directory, invitation history, token-rotating
resend, explicit revocation, and permission-aware People UI passed backend, component, and live
desktop/mobile verification on 2026-07-20. Remaining work includes broader administration lifecycle,
advanced queues, tenant-scoped analytics, API keys, signed webhooks, exports/imports, and production
outbound delivery integration.

## Later phases

7. PostgreSQL RLS, requester binary attachment upload/download with object-storage completion, observability, accessibility/performance/security hardening, production frontend serving, deployment docs, and demo data.

## Frontend clarification

ResolveHub now has a custom end-user frontend with secure authentication and verified requester, agent, and administrator workflows. FastAPI Swagger, Mailpit, and Temporal's optional operator UI remain development/operations interfaces, not the product UI. Phase 6 people lifecycle management is now available; requester binary attachments remain coupled to Phase 7 object storage.

No later phase begins until the preceding milestone's checks and acceptance tests pass.
The exact required backend, frontend, and live end-to-end checks are defined in the
[phase completion gates](testing/phase-gates.md).
