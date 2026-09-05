# Stage 05: Operations and Production Readiness

Status: In Progress

## Objective

Make the completed bot reproducible, observable, recoverable, and safe to
operate in a containerized environment.

This stage is split into separate reviewable PRs (database migrations,
rate limiting, and the remaining observability/CI work).

## Dependencies

- Stages 01–04

## Scope

- [x] Add Alembic migrations for the supported database engines.
- [x] Verify PostgreSQL compatibility without changing service contracts.
- [x] Add configurable rate limiting with an explicit storage strategy.
- [x] Add structured logging, health/startup diagnostics, and error monitoring
  hooks.
- [ ] Document backup, restore, rollout, and rollback procedures.
- [ ] Add CI checks for lint, tests, type checks, and Docker build.

## Acceptance criteria

- [x] A fresh deployment can initialize or migrate the database reproducibly.
- [x] Application services work against SQLite tests and PostgreSQL integration
  tests.
- [x] Rate limits are configurable and fail safely under storage failure.
- [x] Logs contain actionable correlation context without tokens or user
  secrets.
- [ ] CI blocks merges when required checks fail.
- [ ] Deployment and recovery runbooks are checked into the repository.

## Verification

```bash
uv run ruff check .
uv run pytest
docker compose config -q
docker build --tag dano-bot:ci .
```

## PR

Suggested title: `chore(operations): harden deployment and observability`

Split database migrations, rate limiting, and CI into separate PRs if the
implementation becomes larger than one reviewable change.
