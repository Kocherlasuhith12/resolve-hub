# Phase 4 — search and optional AI assistance

## Status

Complete and verified on 2026-07-17.

## Objective

Add tenant-isolated PostgreSQL full-text search first, then introduce optional AI suggestions behind a replaceable provider boundary. ResolveHub must remain fully functional when AI is disabled or unavailable, and every AI result must remain a human-reviewed suggestion.

## Planned files

Initial search slice:

- `resolvehub/app/modules/search/`: request/response schemas, service rules, and thin routes.
- `resolvehub/app/main.py`: search router registration.
- `migrations/versions/20260717_0004_phase4_search_foundation.py`: PostgreSQL GIN full-text indexes.
- `tests/integration/test_phase4_search_ai.py`: search success, filters, visibility, pagination, and cross-tenant denial.
- `docs/phases/phase-4.md`, `docs/progress.md`, `docs/roadmap.md`, and `README.md`: delivery and usage documentation.

The second Phase 4 slice added `ai_assistance` provider contracts, deterministic fakes, suggestion/audit models, and human acceptance/rejection operations. pgvector was independently reviewed and deferred in ADR 001 because semantic vectors are not yet justified by a real embedding model and relevance evaluation.

## Database changes

The first migration adds PostgreSQL GIN expression indexes for searchable ticket text, comments, category text, and requester display names. The second adds tenant-owned AI run/suggestion audit tables and AI permissions. No external search service or vector extension was added.

## Security considerations

- Every search query is constrained by `organisation_id` before results are returned.
- Membership and `ticket:read` are revalidated in the search service.
- Users without `ticket:read_all` can search only their own tickets.
- Internal-note text participates in search only for memberships with `internal_note:read`.
- Search responses return normal ticket boundary schemas and never expose matched private text snippets.
- Query length and result limits are bounded; pagination is cursor based.
- AI is disabled by default and remains isolated behind its provider boundary and audit behavior.

## Acceptance criteria

- Ticket number, title, description, category, permitted requester name, and permitted comments are searchable using PostgreSQL full-text search.
- Status, priority, department, assignee, category, requester, date, and SLA filters compose with search.
- Requesters cannot discover other requesters' tickets or private internal notes.
- A member of another organisation cannot search the target organisation.
- Results use bounded cursor pagination.
- PostgreSQL uses deliberate GIN indexes and the migration upgrades/downgrades cleanly.
- The system works with AI disabled; AI failure never blocks ticket submission.
- AI outputs remain suggestions with stored audit metadata and explicit human decisions.
- Formatting, linting, strict typing, migrations, unit tests, integration tests, and security tests pass.

## Current work

The PostgreSQL search foundation is implemented and verified:

- Generated weighted `tsvector` columns cover ticket number/title/description, category name/description, requester display name, and comment body.
- GIN indexes support each searchable vector without introducing another search infrastructure service.
- `GET /api/v1/organisations/{organisation_id}/search/tickets` supports full-text queries, status, priority, department, assignee, category, requester, SLA state, created/updated date bounds, result limits, and cursor pagination.
- The service revalidates membership and permissions, scopes every query by organisation, limits requesters to their own tickets, and excludes internal-note matches from users without `internal_note:read`.
- Focused automation is available through `make test-search`.

## Verification evidence for search slice

- Ruff formatting and linting: passed for 84 files.
- Strict Mypy: passed for the 10 changed Phase 4 source/test targets.
- Focused service tests: 2 passed.
- Focused PostgreSQL search integration/security test: 1 passed.
- Complete suite: 34 passed.
- Measured branch coverage: 71%; configured 70% floor passed.
- Migration `20260717_0004`: upgrade, downgrade to Phase 3, re-upgrade, and `alembic check` passed. Alembic emitted informational warnings that reflected PostgreSQL computed defaults cannot be modified; no schema drift or upgrade operations were detected.
- Running local stack: migrated and rebuilt successfully. Readiness returned database/Redis `ok`, OpenAPI exposed the search route, and a token-safe live flow registered, verified, logged in, created an organisation/category/ticket, returned exactly that ticket from full-text search, and logged out.

## AI assistance delivered

- Optional provider protocol with AI disabled by default.
- Deterministic fake provider for free local development and tests.
- Category, priority, lexical duplicate, summary, and suggested-response outputs.
- Tenant-owned AI run and suggestion audit records containing provider/model/prompt metadata, input fingerprint, latency, confidence, threshold outcome, status, and human decision metadata.
- Separate `ai:suggest` and `ai:review` permissions for organisation administrators and agents.
- Explicit request, list, accept, and reject APIs; suggestions never mutate ticket state automatically.
- Disabled and provider-failure responses return controlled 503 errors without affecting ticket creation or existing ticket state.
- pgvector was deliberately deferred because no real embedding model or relevance dataset currently justifies storing vectors. See [ADR 001](../architecture/adr-001-defer-pgvector.md).

## Final Phase 4 verification

- Ruff formatting and linting: passed for 93 files.
- Strict Mypy: passed for 87 source files in the approved `resolvehub tests` scope.
- Focused Phase 4 unit tests: 5 passed.
- Focused PostgreSQL integration/security workflow: 1 passed.
- Complete suite: 37 passed.
- Measured branch coverage: 72%; configured 70% floor passed.
- Migration `20260717_0005`: upgrade, downgrade to the search revision, re-upgrade, and schema drift check passed.
- Local database migrated and API rebuilt. Readiness returned database/Redis `ok`, and OpenAPI exposes the AI suggestion route.
