# Phase 6 — administration lifecycle, analytics and integrations

## Status

In progress. The first checkpoint—tenant-scoped people administration—was implemented and verified
on 2026-07-20. Analytics, API keys, signed webhooks, exports/imports, production outbound delivery,
and the remaining administration lifecycle work are still pending, so Phase 6 is not marked complete.

## What has been done

- Added a bounded organisation member directory that returns member identity, role, active state,
  and creation time only after both route- and service-level `member:read` authorization.
- Added bounded invitation history with explicit `PENDING`, `ACCEPTED`, `REVOKED`, and `EXPIRED`
  lifecycle state.
- Added an explicit resend operation. It locks the pending invitation, rotates the opaque token hash,
  invalidates the previous token, and extends the expiry by seven days.
- Added an explicit revoke operation. It locks and revokes a pending invitation; accepted invitations
  cannot be revoked and revoked invitations cannot be resent.
- Kept invitation secrets out of history responses. A new raw token is returned once only in local or
  test environments so the existing deterministic verification flow can continue; production
  outbound delivery remains future integration work.
- Added the People administration UI with live member/invitation counts, member identity and role,
  invitation status history, and permission-gated resend/revoke controls.
- Added backend integration, frontend component, and real desktop/mobile browser coverage for the
  lifecycle, including cross-tenant denial.

No database migration was required for this checkpoint because the existing invitation model already
contained the token hash, acceptance, revocation, expiry, and audit timestamps needed by the explicit
operations.

## How it works

The selected organisation ID scopes every people request. The route authenticates the user and the
organisation service independently revalidates active membership and the required permission.

`GET /api/v1/organisations/{organisation_id}/members` joins only memberships and users in that tenant.
`GET /api/v1/organisations/{organisation_id}/invitations` derives each lifecycle state from its
accepted, revoked, and expiry timestamps without returning the stored token hash.

Resend and revoke use dedicated POST operations rather than a generic update endpoint. Resend accepts
only pending invitations, creates a fresh cryptographically random opaque token, stores only its
SHA-256 hash, and returns the raw value once where local/test settings explicitly permit it. Revoke
sets the revocation timestamp and prevents later acceptance or resend. Row locking makes simultaneous
lifecycle changes deterministic.

The React administration workspace loads the role list, member directory, and invitation history
through tenant-keyed TanStack Query entries. Successful create, resend, and revoke mutations
invalidate the invitation query. Controls appear only when the current membership has the exact
permission strings, while FastAPI remains the authoritative authorization boundary.

## Is it working?

Yes, for the delivered people-administration checkpoint.

Verification on 2026-07-20:

- Backend Ruff format/lint: passed for 94 files.
- Backend Mypy strict mode: passed for 87 source files.
- Focused PostgreSQL integration suite: 9 passed in 36.23 seconds.
- Complete PostgreSQL/Redis backend regression: 40 passed in 84.29 seconds.
- Frontend Oxlint: passed with no warnings.
- Frontend TypeScript/Vite production build: passed; 88 modules transformed.
- Frontend Vitest: all 7 component tests passed in 20.75 seconds.
- Live Playwright: all 4 desktop/mobile cases passed in 54.5 seconds against FastAPI, PostgreSQL,
  Redis, and the browser UI.

The focused integration test verifies initial member listing, pending invitation history, token
rotation, rejection of the old token, acceptance with the new token, accepted/revoked state rules,
member-directory updates, permission denial, and cross-tenant denial. The live browser journey also
creates and accepts an Agent invitation, revokes a separate invitation, discovers the accepted agent
as an assignment candidate, assigns a real ticket, and completes the wider product journey.

## Security behavior

- Member and invitation queries are always organisation-scoped and permission-checked in the service.
- Invitation history never exposes raw or hashed secrets.
- Resending rotates instead of reusing a token; the prior token becomes invalid immediately.
- Accepted invitations cannot be revoked, and revoked invitations cannot be resent or accepted.
- Lifecycle mutations use row locks and explicit domain operations.
- Cross-tenant read and mutation attempts are covered by integration tests.

## Remaining Phase 6 work

1. Complete member/role lifecycle administration beyond directory visibility.
2. Add catalogue and SLA edit/deactivate lifecycle operations and advanced queues.
3. Add tenant-scoped analytics and operational exports/imports.
4. Add scoped API keys and signed webhook subscriptions/delivery.
5. Integrate production outbound email delivery without exposing verification, reset, or invitation
   tokens through API responses.
6. Run every phase completion gate again before Phase 6 can be marked complete.
