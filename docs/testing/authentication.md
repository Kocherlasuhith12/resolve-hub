# Authentication verification guide

Last verified: 2026-07-16

## Correct login sequence

1. Call `POST /api/v1/auth/register` with an email, a password of at least 12 characters, and a display name.
2. In local/test mode, copy the returned `verification_token` into `POST /api/v1/auth/verify-email`. Production will deliver this token through an email provider.
3. Call `POST /api/v1/auth/login` with the same email and password.
4. Copy the returned `access_token` into Swagger's **Authorize** dialog as the bearer token. Protected endpoints such as `GET /api/v1/auth/me` will then work.
5. Use the opaque `refresh_token` only with `POST /api/v1/auth/refresh`. Refresh rotates the value, so discard the previous one.

Login before step 2 intentionally returns the generic `AUTHENTICATION_FAILED` response. The same response is used for unknown email, wrong password, inactive account, and unverified account to prevent account discovery.

## Bugs found and fixed

- Successful logins used to increment the five-attempt throttle. Six valid logins within five minutes could therefore be rejected. Only failed authentication now consumes the quota, and a successful login clears earlier failures.
- The Redis throttle key contained the raw IP and email. It now contains only a SHA-256 digest of that tuple.
- Authentication reused one module-level exception instance across requests. Each rejection now creates its own exception, avoiding shared traceback state during concurrent requests.
- Unknown emails skipped Argon2 work while known emails with a wrong password performed it, creating a timing-based account-enumeration signal. Unknown accounts now verify against a process-local dummy hash before returning the same generic error.
- Swagger did not explain that verification is required before login. Registration, verification, and login now describe that sequence, and registration explicitly returns `requires_email_verification`.
- Readiness bypassed request-scoped database dependencies, and the integration fixture could retain asyncpg connections across pytest event loops. Readiness now uses injected dependencies and integration engines use `NullPool`, making repeated test runs independent of event-loop connection state.

## Automated coverage

Run the focused checks with:

```bash
make test-auth
```

The automated checks cover registration enumeration resistance, unverified-account rejection, successful verified login, repeated successful login, failed-attempt throttling, successful-login reset, session listing, logout, access-token rejection after logout, refresh rotation, and refresh-token replay-family revocation.

The rate-limit tests use unique email identities so Redis state cannot make repeated or reordered test runs produce false failures.

## Verification evidence

On 2026-07-16, Ruff formatting/linting and strict Mypy passed. The focused authentication suite passed twice consecutively (`10 passed` each run). The complete suite then passed with `31 passed` and 70% branch coverage, meeting the configured 70% floor. A separate live Docker smoke test covered register, verify, login, current-user lookup, refresh rotation, logout, and post-logout access rejection without printing tokens.
