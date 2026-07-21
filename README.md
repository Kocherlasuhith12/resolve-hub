# ResolveHub

ResolveHub is a multi-tenant, real-time, AI-assisted service-request and operations platform. It is being built incrementally as a modular Python monolith, with tenant isolation and auditable security boundaries treated as domain invariants.

## Current milestone

Phases 1 through 5 provide the application foundation, secure identity and tenant plane, service catalogue, idempotent ticket operations, business-time SLA policies, durable Temporal warning/breach workflows, transactional notifications, tenant-scoped real-time events, PostgreSQL search, optional audited AI suggestions, and the verified responsive React/TypeScript application.

Delivery status and phase-by-phase evidence are maintained in [docs/progress.md](docs/progress.md).

The end-user frontend, binary file storage, analytics, and integrations remain roadmap work and are not represented as complete. AI is disabled by default and currently provides only deterministic local suggestions; it is not an autonomous decision-maker.

## Architecture and stack

The API is FastAPI with Pydantic v2. Persistence uses async SQLAlchemy 2, PostgreSQL, and Alembic. Temporal provides durable SLA execution; Redis distributes real-time events. The service is a modular monolith: modules own their schemas and services while sharing carefully bounded core infrastructure. See [architecture overview](docs/architecture/overview.md) and [roadmap](docs/roadmap.md).

## Setup

Requirements: Docker with Compose. Local Python development additionally requires Python 3.12;
frontend development requires Node.js 22 and npm.

```bash
cp .env.example .env
make up
make migrate
make workers
make dev
```

In another terminal, start the frontend:

```bash
make frontend-install
make frontend-dev
```

The frontend is at `http://localhost:5173`. The API is at `http://localhost:8000`, Swagger UI at `/docs`, health at `/health/live`, Temporal at `localhost:7234`, and Mailpit at `http://localhost:8025`. Verification tokens are returned only when `RH_ENVIRONMENT=local`; production delivery will use an email provider.

## Quality commands

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-search
make test-phase4
make test
make frontend-lint
make frontend-build
make frontend-test
make frontend-e2e
```

Integration tests require `RH_TEST_DATABASE_URL`, pointing to an isolated PostgreSQL database. CI supplies it. Migrations use `make migrate`; create one with `make migration message="short description"` and inspect generated SQL.

## Demo flow

Register, verify using the local-only token, log in, create an organisation, invite Agent and Requester members, and create a department/category. Configure a business calendar and category/priority SLA policy, then submit a ticket with `Idempotency-Key`. Staff can assign and transition it; requester-wait states pause its SLA. Notification APIs and authenticated WebSockets remain tenant/recipient scoped.

In Swagger, registration must be followed by `/auth/verify-email` before `/auth/login`. After login, paste the returned `access_token` into **Authorize**; do not paste the refresh token there. See the [authentication verification guide](docs/testing/authentication.md) for the exact flow and focused regression command.

Accessible tickets can be searched at `GET /api/v1/organisations/{organisation_id}/search/tickets`. Search covers ticket text, categories, requester display names, and only comments the current membership may see; filters and cursor pagination compose with the query.

Authorised administrators and agents can request optional suggestions under `/api/v1/organisations/{organisation_id}/tickets/{ticket_id}/ai`. Set `RH_AI_ENABLED=true` to use the deterministic local fake. Suggestions are audited and require explicit accept/reject decisions; acceptance records human feedback but does not automatically modify the ticket.

ResolveHub now has responsive sign-in, account creation, local email verification, organisation/catalogue setup, requester ticket workflows, a permission-backed agent queue with eligible-agent assignment, administration creation, permission-aware navigation, personal notifications, authenticated real-time refresh, coordinated 401 recovery, and manual AI suggestion review in `frontend/`. Browser refresh credentials remain in an HttpOnly cookie, CSRF values are bound to the server session, and the access token stays in memory—including when it authenticates WebSockets as a subprotocol rather than a URL value. Phase 5 is complete. Phase 6 is in progress with a verified tenant member directory and invitation history/resend/revoke lifecycle; analytics and integrations remain pending. Binary attachments and production hardening remain Phase 7 work.

## Security model and limitations

Opaque verification and refresh tokens are stored only as SHA-256 hashes. Refresh tokens rotate; replay revokes the complete token family. Passwords use Argon2id. Tenant services revalidate membership and permission, and tests exercise cross-tenant denial. Application-enforced isolation remains in place until PostgreSQL row-level security in Phase 7. External email delivery, password reset, the complete role-management API, production Temporal/Redis deployment, and deployment configuration are not yet implemented.

Licensed under the terms selected by the repository owner; no licence file has yet been chosen.
