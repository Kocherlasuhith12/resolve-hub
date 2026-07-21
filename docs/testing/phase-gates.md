# Phase completion gates

No ResolveHub phase may be marked complete from implementation alone. Each phase report must record
the exact commands and observed results for every applicable gate below.

## Required gates

1. Backend formatting, Ruff lint, and strict Mypy must pass.
2. The complete backend unit and PostgreSQL/Redis integration suite must pass. New resources require
   success, failure, permission, and cross-tenant denial coverage.
3. Frontend lint, TypeScript production build, and component tests must pass.
4. Deterministic Playwright tests must pass on desktop and mobile Chromium.
5. A live Playwright journey must pass through the real frontend, FastAPI API, PostgreSQL, and Redis
   on desktop and mobile for the delivered user workflow.
6. Required runtime dependencies must report ready before live tests begin. A dependency failure is
   reported as a failed gate, not hidden or converted into a passing result.
7. The phase report and [delivery progress](../progress.md) must explain what was delivered, how it
   works, what passed, any failures found and corrected, and what remains incomplete.

External services that are intentionally represented by deterministic fakes must be identified in
the phase report. A fake-provider pass must never be described as a real provider integration.
