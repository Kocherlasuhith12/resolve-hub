# ResolveHub delivery progress

Last updated: 2026-07-20

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 0 | Discovery, architecture, permanent rules, roadmap | Complete | [Phase 0 report](phases/phase-0.md) |
| 1 | Foundation, identity, sessions, organisations, RBAC, invitations, departments | Complete | [Phase 1 report](phases/phase-1.md) |
| 2 | Catalogue, ticket core, events, comments, concurrency, idempotency, metadata | Complete | [Phase 2 report](phases/phase-2.md) |
| 3 | Temporal SLA workflows, outbox, notifications, WebSockets | Complete | [Phase 3 report](phases/phase-3.md) |
| 4 | PostgreSQL search and optional AI assistance | Complete | [Phase 4 report](phases/phase-4.md) |
| 5 | Responsive TypeScript end-user frontend | Complete | [Phase 5 report](phases/phase-5.md) |
| 6 | Administration lifecycle, analytics and integrations | In progress | [Phase 6 report](phases/phase-6.md) |
| 7 | RLS, storage completion, observability and production hardening | Not started | — |

## Current working point

Phases 0–5 are implemented and verified. Phase 6 is now in progress. Its first checkpoint, tenant-scoped people administration, was implemented and verified on 2026-07-20 with member directory, invitation history, token-rotating resend, explicit revocation, permission and tenant isolation, and frontend/backend/live desktop/mobile coverage. Analytics, integrations, and the remaining lifecycle work are still pending. Infrastructure-dependent binary attachments remain sequenced with Phase 7 object storage.

Every phase is now governed by the documented [frontend/backend completion gates](testing/phase-gates.md). A phase cannot be marked complete until its full backend regression and live desktop/mobile frontend-to-backend journey pass and the phase report records the evidence.

Phase 4 is complete. PostgreSQL generated search vectors and GIN indexes cover tickets, comments, categories, and requester display names. Optional AI assistance is disabled by default and uses a replaceable provider contract, deterministic fake, audited runs/suggestions, confidence thresholds, lexical duplicate candidates, explicit human accept/reject decisions, tenant permissions, and failure isolation. AI suggestions never mutate tickets automatically.

The local Docker database was migrated to Phase 4 and the API was rebuilt on 2026-07-17. Readiness and OpenAPI passed, and a live token-safe ticket creation/search/logout smoke flow returned the expected single ticket.

There is now a custom frontend at `frontend/`. It is runnable at `http://localhost:5173` and connects to FastAPI through the Vite `/api` and WebSocket proxy. Registration, local email verification, password login, rotating session recovery/logout, first-organisation/catalogue setup, requester and agent ticket journeys, assignment to eligible agents, supported administration creation, personal notifications, authenticated real-time refresh, and manual AI review work. The Phase 6 People area now also lists tenant members and invitation history and supports safe resend/revoke operations. Object-storage attachments, production outbound delivery, analytics/integrations, and production hardening remain later work.

The complete Phase 3 Docker runtime was launched locally on 2026-07-16. API liveness/readiness, database, Redis, Temporal cluster health, and workflow/activity pollers were verified.

Authentication maintenance was completed on 2026-07-16. The reported login failure was reproduced as an expected rejection before email verification. The verified login flow works; throttle-accounting, privacy, exception-lifecycle, readiness dependency, and test connection-lifecycle issues found during the audit were fixed. Focused tests passed twice consecutively (10 each); the full suite passed with 31 tests and 70% branch coverage. Details are in the [authentication verification guide](testing/authentication.md).

## Working product flow so far

1. A person registers, verifies their email, and logs in.
2. They create an organisation, which receives permission-backed Admin, Agent, Requester, and Auditor roles.
3. An administrator invites users and creates departments.
4. An administrator configures service categories.
5. A requester submits a ticket with an idempotency key.
6. Authorised staff assign and transition the ticket through the controlled state machine.
7. Public comments, private internal notes, attachment metadata, and immutable events build the timeline.
8. Version checks prevent silent concurrent overwrites, and tenant checks protect every ticket operation.
9. A matching SLA policy calculates UTC deadlines from tenant business hours and holidays.
10. Temporal maintains warning/breach timers while ticket transitions pause, resume, or complete the SLA.
11. Transactional outbox workers create personal notifications and publish minimal tenant-scoped events.
12. Authenticated WebSockets deliver only events the current member is permitted to see.
13. Authorised users search only tickets and comment text visible to them within the selected organisation.
14. Authorised staff can request optional audited AI suggestions and explicitly accept or reject them without automatic ticket mutation.
15. A verified user can sign in through the responsive browser UI, restore a rotating cookie/CSRF session, load their account, and sign out with server-side revocation.
16. A new user can create an account with email and password, complete local verification, log in, create their first organisation, and select that authorised tenant.
17. Within the selected tenant, an authorised user can configure the first service category, submit an idempotent ticket, and browse a bounded cursor-paginated request list.
18. A requester can open an authorised ticket, read its status, description, SLA facts, public conversation and event timeline, then add a public reply.
19. A requester can search authorised ticket and public-comment text within the selected organisation and return to a matching request.
20. The UI loads the current membership's authoritative permission strings and exposes an organisation-wide agent queue only to memberships with `ticket:read_all`.
21. Authorised staff can filter the queue, self-assign with optimistic version checks, use explicit allowed state transitions, view SLA facts, and create visibly separated internal notes.
22. Authorised administrators can create invitations, departments, service categories, weekday business calendars, holidays, and category/priority SLA policies from the selected tenant.
23. A ticket created after matching SLA configuration receives live business-time response/resolution deadlines and displays an active SLA in the agent detail screen.
24. Members with `notification:read` can browse only their tenant-scoped personal notifications and mark their own items read.
25. The browser authenticates its organisation WebSocket with an in-memory bearer subprotocol, refreshes notification and ticket queries on permitted events, and falls back to bounded polling when disconnected.
26. Staff with `ai:suggest` can request optional audited recommendations; staff with `ai:review` can explicitly accept or reject each result after inspecting confidence and threshold status.
27. AI decisions record human feedback only. They do not change ticket category, priority, state, summary, comments, or assignment.
28. Concurrent protected requests that receive 401 share one CSRF-protected refresh rotation and each replay once; terminal failure clears authentication and cached tenant data.
29. Permission-aware navigation exposes only Requests, Notifications, and Administration sections authorised by the selected membership.
30. Staff with `ticket:assign` receive a tenant-scoped list containing only active `ticket:read_all` members and can assign a ticket to another eligible agent with optimistic version protection.
31. Administrators with `member:read` can browse the selected tenant's member directory and invitation history without exposing invitation secrets.
32. Administrators with `member:invite` can rotate a pending invitation token or revoke the invitation through explicit lifecycle operations; accepted and revoked state rules are enforced by the backend.
