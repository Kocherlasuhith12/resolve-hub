# ResolveHub frontend

React and TypeScript frontend for ResolveHub Phase 5. It currently supports account creation,
local email verification, password login, secure browser sessions, first-organisation/catalogue
setup, and requester ticket creation/listing.
The requester can also open ticket detail, post public replies, review the event timeline, and
search authorised requests within the selected organisation.
Membership permission strings also drive an agent queue with status/priority filters, self-assignment,
eligible-agent assignment, explicit ticket transitions, SLA facts, and visibly separated internal notes. Backend permissions,
tenant checks, and optimistic versions remain authoritative.
Administrators with the corresponding permission strings can also create invitations, browse the
tenant member directory and invitation history, rotate pending invitation tokens, revoke pending
invitations, and create additional departments/categories, weekday business calendars, holidays,
and SLA policies.
Members with `notification:read` also receive a bounded personal notification center with read state.
Authenticated tenant WebSockets refresh notifications and affected ticket queries; a bounded polling
fallback is used while disconnected. The access token remains in memory and is sent as a WebSocket
subprotocol, never in the URL.
Staff with `ai:suggest` can request optional audited recommendations from ticket detail, while
`ai:review` controls explicit accept/reject actions. Confidence and threshold state stay visible,
and decisions record feedback only—they never apply category, priority, response, or other ticket
changes automatically. The deterministic fake provider is disabled by default and can be enabled
locally with `RH_AI_ENABLED=true`.
Protected 401 responses use one shared CSRF-protected refresh rotation and retry once. Terminal
session failure clears cached tenant state. Responsive workspace navigation shows only sections
allowed by the selected membership's permission strings.
Vite serves the app on
`http://localhost:5173` and proxies `/api` HTTP and WebSocket traffic to FastAPI on
`http://127.0.0.1:8000`.

```bash
npm install
npm run dev
```

Quality commands:

```bash
npm run lint
npm run build
npm test
npm run test:e2e
LIVE_API=true npm run test:e2e
```

The default Playwright journey uses deterministic API interception. Live mode requires the local
API, Redis, and PostgreSQL stack and creates isolated local-only verified accounts. The architecture
and browser-session design are documented in
[`docs/architecture/adr-002-frontend-and-browser-auth.md`](../docs/architecture/adr-002-frontend-and-browser-auth.md).
