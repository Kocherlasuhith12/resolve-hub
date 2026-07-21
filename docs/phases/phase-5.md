# Phase 5 — responsive end-user frontend

## Status

Complete. Architecture, secure authentication, registration/verification, first-organisation
setup, and requester ticket create/list/detail/reply/timeline/search checkpoints completed and
verified on 2026-07-18. The first permission-aware agent queue, assignment, transition, internal-note,
and SLA checkpoint is also complete. The supported administration creation checkpoint—invitation,
department/category, calendar, holiday, and SLA policy—is complete as well. The personal
notification and authenticated real-time refresh checkpoint was completed on 2026-07-19. The
optional AI suggestion and explicit human-review checkpoint was completed on 2026-07-20.
Coordinated 401 recovery, permission-aware navigation, and broader eligible-agent assignment were
completed and verified on 2026-07-20. Dependency-bound follow-up work is explicitly assigned to
Phases 6 and 7 below and is not claimed as a Phase 5 capability.

## What has been done

- Accepted [ADR 002](../architecture/adr-002-frontend-and-browser-auth.md): React 19, TypeScript,
  Vite, React Router, TanStack Query, WCAG 2.2 AA target, same-site production deployment, and the
  browser authentication boundary.
- Created the `frontend/` workspace with a responsive login experience and authenticated
  application shell for desktop and phone layouts.
- Added visible Sign in and Create account options, password confirmation, email verification,
  verified-email handoff back to login, and enumeration-safe registration messaging.
- Added a typed API client, in-memory access token, startup refresh recovery, shared error handling,
  authenticated user loading, protected routes, and logout.
- Added browser-specific backend endpoints for login, refresh, and logout while preserving the
  existing token-pair endpoints for non-browser clients.
- Added Alembic migration `20260718_0006`, which stores only a SHA-256 CSRF token hash on the auth
  session.
- Added component tests, deterministic mocked Playwright coverage, and an opt-in live Playwright
  journey that registers, verifies, signs in through the UI, loads the authenticated user, creates
  and selects an organisation, configures a service, creates and opens a ticket, posts a public
  reply, searches, and signs out against the real API and PostgreSQL database.
- Added authenticated organisation discovery, empty-account onboarding, organisation creation, and
  a selected-tenant control using TanStack Query. Backend tenant authorization remains authoritative.
- Added selected-tenant service-category and ticket loading, first department/category setup, a
  requester ticket form, idempotent creation, status/priority cards, 20-item bounded pages, and
  cursor-based load-more behavior.
- Added request detail with status, priority, SLA state, creation time, resolution target, and plain
  text description rendering.
- Added the public conversation and event timeline. The requester UI can post only `PUBLIC`
  comments; private internal notes are neither requested nor rendered.
- Added selected-tenant PostgreSQL-backed search across authorised tickets and visible comment text,
  with a two-character minimum and a bounded 20-result response.
- Added `GET /api/v1/organisations/{organisation_id}/membership/me`, returning only the current
  authorised membership, role display name, and sorted permission strings. Cross-tenant access is
  denied and the UI never branches on role names.
- Added an organisation-wide agent queue for memberships with `ticket:read_all`, including bounded
  status and priority filters.
- Added permission-gated self-assignment with optimistic ticket versions and explicit state-machine
  transitions. The UI offers only transitions allowed from the current status and asks for reasons
  where the domain requires them.
- Added staff conversation behavior with clearly marked internal notes. Only memberships with
  `internal_note:create` receive the note control, and backend `internal_note:read` filtering remains
  authoritative for returned comments and timeline events.
- Added SLA state, resolution target, and current assignment visibility to agent ticket detail.
- Added the permanent [phase completion gates](../testing/phase-gates.md), requiring complete backend
  and live desktop/mobile frontend-to-backend verification before any phase is marked complete.
- Added a permission-aware administration workspace. Each panel is driven by exact permission
  strings: `member:invite`/`member:read`, `department:create`, `category:create`, and `sla:manage`.
- Added role-backed invitation creation with local-only acceptance-token display when the backend
  intentionally returns it. Production outbound invitation delivery is not claimed.
- Added additional department and service-category creation with tenant-scoped lists and default
  priority selection.
- Added Monday–Friday business-calendar creation with IANA timezone and opening/closing times,
  holiday creation, and category/calendar/priority SLA-policy creation with bounded response,
  resolution, warning, and requester-wait settings.
- Kept mandatory first-service onboarding separate from the full administration area so duplicated
  catalogue controls are not presented before the first category exists.
- Added a personal notification center only for memberships with `notification:read`. It uses
  bounded cursor pagination, visually distinguishes unread items, and calls the ownership-protected
  backend operation to mark a notification read.
- Added authenticated organisation WebSockets through the Vite proxy. The current in-memory access
  token is sent as a bearer subprotocol, never in a URL, cookie, log, or persisted browser storage.
- Real-time events invalidate tenant-scoped notification, ticket list/detail, comment, and timeline
  queries. A ten-second polling fallback keeps notifications current while the socket is unavailable,
  and reconnection uses bounded exponential delay.
- Added a ticket-detail AI review panel only for memberships with `ai:suggest`. It renders category,
  priority, duplicate, summary, and response suggestions as plain text with confidence and configured
  threshold state instead of exposing raw provider output.
- Added explicit accept/reject controls only for `ai:review`. The interface clearly states that a
  decision records human feedback but does not apply any suggestion or mutate the ticket.
- Added optional Compose passthrough for `RH_AI_ENABLED`, provider, and confidence threshold. The
  deterministic fake remains disabled by default and no external AI-provider capability is claimed.
- Added single-flight access-token recovery. Concurrent protected 401 responses share one rotating,
  CSRF-protected browser refresh and replay each original request exactly once with the new token.
- Terminal refresh or retry failure removes the in-memory token and user, returns to the unauthenticated
  boundary, and clears TanStack Query so one user's tenant data cannot remain for a later login.
- Added responsive Requests, Notifications, and Administration navigation. Section visibility uses
  exact permissions from `/membership/me`; backend authorization remains authoritative.
- Added `GET /api/v1/organisations/{organisation_id}/tickets/assignment-candidates`. It requires
  `ticket:assign`, returns only active tenant members whose role has `ticket:read_all`, and exposes
  only user ID and display name.
- Replaced self-only assignment with an eligible-agent selector while retaining optimistic ticket
  versions and the explicit assignment domain operation.

## Is it working?

Yes. All Phase 5 delivered workflows and completion gates pass.

Verification through 2026-07-20:

- Backend Ruff format/lint: passed, 94 files.
- Backend Mypy strict mode: passed, 87 source files.
- Backend unit tests: 27 passed.
- Focused PostgreSQL authentication integration tests: 9 passed.
- Complete backend suite: 40 passed with 72% branch coverage.
- Current complete backend regression after the agent checkpoint: 40 passed in the isolated Compose
  PostgreSQL/Redis network.
- Focused ticket lifecycle and tenant-isolation integration suite: 2 passed, including current
  membership permissions and cross-tenant denial.
- Frontend Oxlint: passed with no warnings.
- Frontend TypeScript production build: passed; 85 modules transformed.
- Current administration build: passed; 86 modules transformed.
- Frontend Vitest: 5 component tests passed, including password mismatch, register/verify, tenant
  loading, ticket submission/idempotency, detail loading, public reply, timeline, and search behavior.
- Playwright deterministic authentication journey: passed on desktop Chromium and Pixel 7-sized
  mobile Chromium.
- Playwright live API/database journey: passed on desktop and mobile Chromium through visible
  registration, verification, email/password login, organisation creation/selection, first service
  setup, agent queue, real ticket submission/listing, detail, self-assignment, transitions through
  triaged/assigned/in-progress, internal note, public reply, timeline, tenant search, and logout.
- Expanded administration live journey: passed on desktop and mobile Chromium in 2.2 minutes. It
  created a real invitation, second department/category, weekday calendar, holiday, matching SLA
  policy, SLA-active ticket, and completed the agent lifecycle against FastAPI, PostgreSQL, and Redis.
- Current complete backend regression after the administration UI change: 40 passed in 111.71
  seconds; frontend component regression: 5 passed; deterministic Playwright: 2 passed and 2
  intentionally skipped live cases.
- Current notification/real-time frontend gates: Oxlint passed; TypeScript/Vite production build
  passed with 87 modules transformed; all 5 component tests passed in 16.49 seconds.
- Current deterministic Playwright: 2 passed with the 2 opt-in live cases intentionally skipped.
- Current complete backend regression: 40 passed against PostgreSQL and Redis in 310.19 seconds;
  Ruff passed for 94 files and Mypy passed for 87 source files.
- Current live desktop/mobile suite: all 4 cases passed serially in 29.9 seconds. The real journey
  verified registration through logout plus notification delivery, authenticated live-update state,
  and marking the delivered ticket notification read through FastAPI, PostgreSQL, the outbox worker,
  Redis, and WebSockets.
- Current AI-review frontend gates: Oxlint passed; TypeScript/Vite production build passed with 88
  modules transformed; all 5 component tests passed in 12.65 seconds.
- Current AI-review deterministic Playwright: 2 passed in 8.0 seconds with the 2 opt-in live cases
  intentionally skipped.
- Current AI-review backend gates: Ruff passed for 94 files, Mypy passed for 87 source files, and the
  complete PostgreSQL/Redis suite passed all 40 tests in 56.57 seconds.
- Current AI-enabled live desktop/mobile suite: all 4 cases passed serially in 36.1 seconds. The real
  journey generated five suggestions, accepted the priority suggestion, rejected the below-threshold
  duplicate suggestion, and verified that the ticket priority remained unchanged.
- Final frontend gates: Oxlint passed; TypeScript/Vite production build passed with 88 modules;
  all 7 component tests passed in 12.70 seconds. The new tests cover single-flight concurrent refresh,
  exactly-once replay, terminal refresh failure, tenant-cache clearing, navigation, and assignment.
- Final backend gates after rebuilding the development image: Ruff passed for 94 files, Mypy passed
  for 87 source files, and all 40 PostgreSQL/Redis tests passed in 224.93 seconds. Assignment candidates
  include success plus requester and cross-tenant denial coverage.
- Final deterministic Playwright: 2 desktop/mobile authentication cases passed in 4.9 seconds; the 2
  opt-in live cases were intentionally skipped.
- Final live Playwright: all 4 cases passed serially in 33.9 seconds. The real desktop/mobile journey
  registered and verified a second user, accepted an Agent invitation, discovered that active eligible
  member, assigned the ticket to “Browser Agent,” and completed notifications, AI review, transitions,
  comments, search, and logout through the real stack.
- Token-safe live API smoke: register 202, verify 204, browser login 200, refresh 200, current user
  200, logout 204, and both browser cookies cleared.
- Live Compose database migrated from `20260717_0005` to `20260718_0006`; API rebuilt and restarted.

Initial live desktop runs exposed two environment timing limits while Argon2 shared CPU with other
Docker workloads: the default 30-second test budget during registration and then the default
five-second post-submit assertion. The live-only test now has a bounded 120-second test budget and
60-second post-submit assertion; the final rerun passed on desktop and mobile.

The expanded agent journey found and corrected a reply-form defect where the previous public reply
could remain in the textarea and be prefixed to a following internal note. Controlled form state now
clears the body after a successful post, and the component regression verifies the two messages stay
separate. The backend test fixture also used a bare `alembic` command; it now launches Alembic through
the active Python interpreter so documented virtual-environment commands are reproducible.

The first live rerun began before the rebuilt API accepted traffic, so registration showed the shared
network error. The live suite now polls `/health/ready` before registering. The longer agent journey
also exceeded the earlier requester-only 120-second whole-test ceiling under Docker CPU contention;
the live-only ceiling is now 240 seconds while each user-visible assertion remains bounded. The final
desktop/mobile rerun passed in 1.5 minutes. After the final destination-specific permission review,
the unchanged live workflow passed again on both browsers in 26.9 seconds.

An initial full-suite container run reported 38 passed and two Redis-dependent failures because its
Redis URL incorrectly pointed to container-localhost. With the Compose Redis address supplied,
readiness and login throttling behaved correctly and all 40 tests passed. No dependency failure was
suppressed or converted into a pass.

The first administration browser run exposed overlapping first-onboarding and administration labels.
The full administration area now stays hidden until the mandatory first category exists, and its
fields use explicit names such as “New department name” and “Department description.” Later runs
also exposed Playwright substring/label ambiguity between the catalogue and ticket forms; exact
semantic or stable form-name selection now protects the intended field. The final desktop/mobile
journey passed without skipping any administration or ticket step.

The first notification live run started desktop and mobile registration password hashing in parallel
immediately after the complete backend container run. Both registration requests remained pending
under local Docker CPU contention and timed out before reaching the new workflow. The unchanged
desktop/mobile assertions passed serially in 29.9 seconds; no notification, WebSocket, or security
check was skipped. The first sandboxed deterministic Playwright launch was also unable to bind port
5173 (`EPERM`); the approved local-server rerun passed.

The final backend image command initially requested a nonexistent Docker stage named `test`; the
Dockerfile defines `development`. The correct development image was rebuilt before the final suite,
so no stale backend code was tested. Ruff also found and mechanically corrected one import-order
issue. A component assertion that inspected a case-sensitive header object was updated to use the
Fetch `Headers` API after request-header normalization; the idempotency header itself was present.

## How it works

1. A person chooses Create account and submits their name, email address, password, and matching
   confirmation. The API always returns enumeration-safe registration messaging.
2. Login remains locked until `/api/v1/auth/verify-email` accepts the opaque verification token.
   Local/test mode returns this token to the verification screen; production outbound email delivery
   is not implemented yet.
3. The UI sends verified credentials to `/api/v1/auth/browser/login` with
   `X-ResolveHub-Client: browser`.
4. FastAPI applies the existing enumeration-resistant authentication and login throttling.
5. The response returns a short-lived access token and session-bound CSRF token. The rotating
   refresh credential is set only as an HttpOnly, SameSite cookie and never appears in JSON.
6. The UI keeps the access token in memory, loads `/auth/me`, and renders protected routes.
7. The authenticated shell lists the user's organisations. A new user can create their first
   organisation and select it as the tenant context for following screens.
8. The selected tenant loads only its authorised service categories and tickets. If its catalogue is
   empty, an administrator can configure the first department/category.
9. Request creation sends a fresh `Idempotency-Key`; the list uses a maximum page size of 20 and
   follows only opaque cursors returned by the API.
10. Selecting a ticket loads its tenant-authorised detail, the first 20 public comments, and the
    first 20 immutable timeline events. Posting a reply always sends `kind: PUBLIC`, then refreshes
    both conversation and timeline queries.
11. Search sends the selected organisation and trimmed query to the existing permission-scoped
    PostgreSQL full-text endpoint. Search results never bypass backend membership checks.
12. On page restoration, the readable CSRF cookie is sent as `X-CSRF-Token`; the backend compares
   cookie/header values and the session-bound server hash before rotating refresh and CSRF values.
13. Logout uses the bearer access token, revokes the server-side session, and clears both cookies.
14. Backend permissions and tenant checks remain authoritative; the browser shell does not make
   authorization decisions.
15. The selected organisation loads `/membership/me`; the browser uses returned permission strings
    to choose requester or agent presentation without role-name conditionals.
16. Staff queue filters compose with the existing tenant-scoped ticket endpoint. Self-assignment
    calls the explicit assignment operation with the displayed version, then refreshes detail,
    queue, and timeline data.
17. Status changes call the explicit transition operation. The backend locks the row, checks the
    expected version and permission, validates the state graph and required reason, writes the event,
    and returns the new version.
18. Internal notes use the same comment endpoint with `kind: INTERNAL`; server-side permissions and
    response filtering ensure requesters receive neither note bodies nor internal timeline events.
19. Administration independently loads the current membership and returns no interface for users
    without an applicable administration permission.
20. Invitation role options come from the selected organisation's permission-protected role list;
    creation uses the backend's expiring opaque invitation operation.
21. Department/category mutations refresh tenant-scoped catalogue queries shared with ticket forms.
22. Calendar creation converts the chosen weekday interval into the validated weekly-hours schema.
    Holiday and policy forms appear only after their required calendar/category records exist.
23. SLA policy creation remains an explicit backend operation. A matching ticket receives calculated
    UTC deadlines atomically at creation; the browser only renders the returned SLA state and dates.
24. The notification center reuses `/membership/me` and renders only when the backend-provided
    permission set contains `notification:read`; the API still independently checks membership,
    tenant, permission, and notification ownership.
25. Notification pages request at most 20 items and follow only backend-issued opaque cursors.
    Mark-read posts the notification ID within the selected organisation and refreshes that tenant's
    notification cache.
26. The browser opens `/api/v1/organisations/{organisation_id}/ws` with `bearer` and the in-memory
    access token as WebSocket subprotocols. FastAPI revalidates the live auth session, active user,
    active membership, recipients, and staff visibility before accepting or forwarding an event.
27. A permitted event refreshes only the selected tenant's relevant cached queries. Socket failure
    switches the visible status to polling and schedules a bounded reconnect; component unmount or
    tenant selection change closes the old socket and cancels its timer.
28. The AI panel appears only with `ai:suggest`; the backend independently checks that permission,
    ticket access, and organisation scope before calling the configured provider.
29. Provider output is stored as audited suggestions with provider/model/prompt metadata, confidence,
    threshold result, and an input fingerprint. Provider failure or disabled configuration returns a
    contained availability message and does not interrupt ordinary ticket operations.
30. Accept and reject buttons require `ai:review`. The decision endpoint locks the tenant-owned
    pending suggestion, rejects repeated decisions, and records the reviewer and UTC decision time.
31. Neither acceptance nor rejection executes a ticket update. Suggested category, priority,
    duplicate IDs, summary, and response remain advisory until a person performs a separate explicit
    domain operation.
32. Protected API calls keep the access token in a ref as well as React state. On 401, the first call
    starts browser refresh and concurrent calls await that same promise, preventing refresh-token
    rotation reuse.
33. Each failed protected call retries once with the rotated access token. A second 401 or refresh
    failure clears authentication and all cached server data; non-401 errors never trigger refresh.
34. Workspace navigation is presentation only: it reads exact membership permissions to hide
    irrelevant sections, while every mounted query and mutation still passes backend tenant and
    permission checks.
35. Assignment candidates are selected by organisation, active membership/user state, and the
    `ticket:read_all` permission. Assignment then revalidates the target and ticket version inside the
    existing locked domain operation.

## Run it

With the API and dependencies running:

```bash
make up
make migrate
make dev
```

In another terminal:

```bash
make frontend-install
make frontend-dev
```

Open `http://localhost:5173`. Choose Create account, complete the local verification screen, and
sign in with the registered email address and password.

If another host PostgreSQL service owns port 5432, run the migration inside the project network:

```bash
docker compose run --rm api alembic upgrade head
```

Frontend verification commands:

```bash
make frontend-lint
make frontend-build
make frontend-test
make frontend-e2e
LIVE_API=true make frontend-e2e
```

The normal Playwright run uses deterministic API interception. `LIVE_API=true` requires the local
API and database and exercises the delivered requester-to-agent-to-administrator workflow end to
end.

The optional deterministic local provider remains off by default. Enable it for a local review run
with `RH_AI_ENABLED=true docker compose up -d api` before starting the live browser suite.

## Security behavior

- Long-lived refresh credentials are not placed in `localStorage`, `sessionStorage`, application
  state, response JSON, logs, or URLs.
- CSRF requires a matching cookie, custom header, and server-side session hash. SameSite is
  defense-in-depth, not the sole control.
- Staging and production configuration is rejected unless `RH_BROWSER_COOKIE_SECURE=true`.
- CORS origins are explicit and the custom browser header forces a non-simple request.
- The UI renders plain React text and makes no unsanitised HTML insertion.
- Keyboard focus is visible, labels are explicit, reduced-motion preferences are honored, and the
  layout has desktop and mobile browser coverage.

## Explicit follow-up scope

- Phase 6 begins with member listing, invitation history/revocation/resend, catalogue/SLA lifecycle
  editing, role management, and advanced queues, then continues with analytics and integrations.
- Production outbound delivery belongs with the Phase 6 integration work. Local/test opaque-token
  handoff remains explicit; no production mail-provider delivery is claimed.
- Requester binary attachment upload/download remains coupled to Phase 7 S3-compatible object storage.
  Phase 2 attachment metadata is not described as a binary upload.
- Broader accessibility auditing, production frontend serving, CSP/security hardening, observability,
  and deployment work remain Phase 7 hardening.
