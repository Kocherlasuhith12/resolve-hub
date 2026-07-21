# ADR 002 — frontend architecture and browser authentication

- Status: accepted
- Date: 2026-07-18
- Phase: 5

## Context

ResolveHub has a versioned FastAPI JSON API and no end-user interface. The first frontend must
support requester, agent, and administrator workflows without moving permission or tenant decisions
into the browser. The existing JSON refresh-token endpoint remains useful for non-browser API
clients, but persisting that long-lived token in browser storage would unnecessarily expose it to
JavaScript.

## Decision

Build a standalone React and TypeScript single-page application in `frontend/`, using Vite for the
development/build pipeline, React Router for route boundaries, and TanStack Query for server-state
coordination. Use semantic HTML and target WCAG 2.2 AA. Production should expose the built frontend
and `/api/v1` from the same site; Vite proxies `/api` to FastAPI during local development.

Browser authentication uses dedicated `/api/v1/auth/browser/*` endpoints:

- a short-lived access token is returned to and retained only in application memory;
- the rotating refresh token is stored in an HttpOnly, SameSite cookie and is never returned in a
  browser-auth response body;
- a random CSRF token is bound to the server-side auth session by its SHA-256 hash, returned after
  login/refresh, and mirrored in a non-HttpOnly SameSite cookie so a page reload can recover it;
- refresh requires the CSRF cookie and matching `X-CSRF-Token` header, and the server verifies the
  session-bound hash before rotating either token;
- browser login and refresh require `X-ResolveHub-Client: browser`, making them non-simple CORS
  requests; configured origins remain explicit and credentialed;
- logout requires the bearer access token, revokes the server session, and clears both cookies.

The existing `/auth/login` and `/auth/refresh` token-pair contracts remain unchanged for trusted
non-browser clients. Backend authorization remains authoritative for every UI route and action.

Testing uses Vitest and Testing Library for components and Playwright for real browser journeys.
Playwright begins with the authentication shell and expands with each delivered workflow.

## Consequences

- A database migration adds a nullable CSRF hash to auth sessions; existing API sessions continue to
  work without one.
- Local HTTP development explicitly disables the Secure cookie flag. Staging and production
  configuration must enable it.
- XSS can still make requests as the current user, so the UI must not render unsanitised HTML and a
  restrictive content-security policy remains production-hardening work.
- Cross-origin production deployment is unsupported by default. Any exception requires an explicit
  threat review of origins, cookies, proxies, and CSRF behavior.

## References

- React recommends Vite as a build option for a from-scratch TypeScript application.
- OWASP recommends HttpOnly for session credentials and a session-bound CSRF token in a custom
  request header; SameSite is defense in depth rather than the only control.
- Playwright is the selected end-to-end runner for critical browser and permission journeys.
