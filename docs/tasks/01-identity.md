# Stage 01: Identity and Authorization

Status: Done

## Objective

Persist Telegram users and administrators, and centralize authorization so
every future admin handler uses the same policy.

## Dependencies

- Stage 00

## Scope

- Add `User` and `Admin` persistence models with unique Telegram IDs.
- Add repository methods for get-or-create user and admin lookup.
- Seed configured administrators idempotently.
- Add authorization tests for allowed, denied, and missing-user cases.
- Keep the existing settings-based bootstrap compatible during migration.

## Acceptance criteria

- [x] Repeated startup does not create duplicate administrators.
- [x] User identity is persisted without storing secrets.
- [x] Admin authorization is available through one reusable filter/service.
- [x] Handlers do not query SQLModel sessions directly.
- [x] SQLite tests pass with an isolated database.

## Verification

```bash
uv run ruff check .
uv run pytest tests/database tests/router
```

## PR

Suggested title: `feat(identity): persist users and administrators`

Do not add content upload, deep-link delivery, or admin-panel screens in this
PR.
