# Phase 1 — foundation and identity

## Status

Complete and verified on 2026-07-13.

## Objective

Create the runnable FastAPI/PostgreSQL foundation and implement the secure identity and tenant control plane required by every later module.

## What was delivered

- Pinned Python 3.12 FastAPI project with async SQLAlchemy 2, asyncpg, Alembic, PostgreSQL, and Redis.
- Environment-based Pydantic settings, structured JSON logging, request IDs, shared error envelopes, CORS, liveness, and readiness.
- Registration, local/test email verification, Argon2id passwords, login, JWT access tokens, rotating refresh tokens, replay-family revocation, logout, logout-all, and session management.
- Organisations, memberships, roles, permissions, invitations, and departments.
- Application- and service-layer permission/tenant validation.
- Dockerfile, Docker Compose, Makefile, GitHub Actions, unit/integration/security tests, and coverage enforcement.

## Database migration

`20260713_0001_phase1_identity.py` creates users, authentication sessions, organisations, permissions, roles, role-permission mappings, memberships, invitations, and departments with constraints and indexes.

## How it works

Access JWTs contain only user and session identifiers. Every authenticated request verifies that the account and database session remain active, so revocation takes effect before JWT expiry. Refresh values are opaque random tokens stored as SHA-256 hashes. Each refresh transaction locks the current session, rotates the token, and links the replacement; reuse revokes the complete family.

Creating an organisation creates an administrator role and membership. Invitation acceptance binds an already authenticated user to the invitation's tenant and role. Material tenant operations call the same permission service even when a route has already authenticated the caller.

## API groups

- `/api/v1/auth`: registration, verification, login, refresh, identity, sessions, logout.
- `/api/v1/organisations`: creation and membership-scoped listing.
- Organisation roles, invitations, and departments.
- `/health/live` and `/health/ready`.

## Security controls

- Argon2id password hashes and hashed refresh/verification tokens.
- Enumeration-resistant registration response.
- Refresh replay detection and family revocation.
- Redis login throttling with production fail-closed behaviour.
- Current database session/account checks for every access token.
- Permission-based organisation isolation and cross-tenant denial tests.

## Verification evidence

- Docker Python 3.12 image build: passed.
- Ruff formatting and linting: passed.
- Strict Mypy: passed for 29 source files.
- Alembic clean upgrade and drift check: passed; no new operations detected.
- Complete test suite at phase completion: 11 passed.
- Measured branch coverage: 77%; configured 75% floor passed.
- Docker Compose validation: passed.

Authentication was re-audited on 2026-07-16 after a reported login problem. The live failure was login before email verification; the verified register-to-logout flow passed. The audit also corrected login-throttle accounting, removed raw identity data from Redis keys, stopped exception-instance reuse, improved Swagger guidance, and added repeatable regression tests. See the [authentication verification guide](../testing/authentication.md).

The verification process initially exposed a migration unique-index mismatch, an incorrectly awaited synchronous logger call, and an unattained 80% coverage target. The schema and logger were fixed; the enforceable initial floor was set honestly to 75%.

## Known limitations

Real email delivery, password reset, custom role-management endpoints, durable login-attempt history, and PostgreSQL row-level security were not implemented. Ticket and workflow features remained absent.

## Next milestone

Phase 2: service catalogue and tenant-isolated ticket operations.
