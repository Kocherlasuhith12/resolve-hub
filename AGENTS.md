# ResolveHub Engineering Rules

ResolveHub is a multi-tenant operations platform built as a modular FastAPI monolith. Keep HTTP handlers thin; place business rules in module services; use SQLAlchemy 2 async sessions and Alembic for every schema change.

## Approved stack

Python 3.12, FastAPI/Pydantic v2, PostgreSQL/asyncpg, SQLAlchemy 2, Alembic, Redis, Temporal (from Phase 3), S3-compatible storage, pytest, Ruff, Mypy, Docker Compose, and GitHub Actions. Do not add overlapping infrastructure without an ADR.

## Commands

Copy `.env.example` to `.env`, then use `make install`, `make up`, `make migrate`, and `make dev`. Quality gates are `make format`, `make lint`, `make typecheck`, and `make test`. Create a migration with `make migration message="description"`; inspect it before applying `make migrate`.

## Permanent rules

- Every tenant-owned row and query carries `organisation_id`. Validate tenant membership and permissions in both route dependencies and service methods. Scope caches, events, search, files, and analytics by tenant. Add cross-tenant denial tests for every resource.
- Store UTC timestamps and UUID public identifiers. Add explicit constraints, indexes, bounded pagination, and transactions for multi-step work.
- Use permission strings, not role-name conditionals. Status changes use explicit domain operations, never generic field updates.
- Never store or log plaintext passwords, refresh/verification/reset tokens, secrets, private file data, or sensitive ticket bodies. Hash opaque tokens; rotate refresh tokens and revoke their family on reuse.
- APIs live under `/api/v1`, use Pydantic boundary schemas, correlation IDs, and the shared error envelope. Never expose stack traces.
- Tests must cover success, failure, permissions, and tenant isolation. Integration tests use PostgreSQL, do not depend on order, and clean up their data. External providers use deterministic fakes.
- A feature is done only with implementation, migration, validation, authorization, tenant isolation, audit behavior where applicable, tests, docs, and passing format/lint/type/test checks.
- Maintain `docs/progress.md` and one `docs/phases/phase-N.md` report per phase. Each report must state the objective, implementation, architecture and user flow, files and migrations, endpoints, security controls, exact verification results, limitations, and next milestone. Never mark a phase complete before its required checks pass.
- Never invent test, benchmark, deployment, or feature results. Do not disable failing tests, commit `.env`, hard-code credentials, edit released migrations casually, or claim production readiness without evidence.
