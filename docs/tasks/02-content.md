# Stage 02: Content Persistence and Upload

Status: Done

## Objective

Allow an authorized administrator to store supported Telegram content metadata
and receive a unique access code, without implementing user delivery yet.

## Dependencies

- Stage 01

## Scope

- Define the content model: source chat, source message, type, code, state,
  creation time, and optional expiration.
- Add repository methods for create, lookup, activate, and deactivate.
- Add a service that generates collision-resistant codes.
- Add an admin router handler for supported uploads.
- Return a link payload from the service; delivery is Stage 03.

## Acceptance criteria

- [x] Only authorized administrators can create content records.
- [x] Generated codes are unique and safe for Telegram deep-link parameters.
- [x] Duplicate code collisions are retried without losing the original request.
- [x] Unsupported messages receive a clear response and are not persisted.
- [x] Service and repository behavior have focused tests.

## Verification

```bash
uv run ruff check .
uv run pytest tests/content tests/router/admin
```

## PR

Suggested title: `feat(content): add administrator content upload`

Do not implement membership checks, content delivery, statistics, or a web
admin panel in this PR.

## Objective

Allow an authorized administrator to store supported Telegram content metadata
and receive a unique access code, without implementing user delivery yet.

## Dependencies

- Stage 01

## Scope

- Define the content model: source chat, source message, type, code, state,
  creation time, and optional expiration.
- Add repository methods for create, lookup, activate, and deactivate.
- Add a service that generates collision-resistant codes.
- Add an admin router handler for supported uploads.
- Return a link payload from the service; delivery is Stage 03.

## Acceptance criteria

- [ ] Only authorized administrators can create content records.
- [ ] Generated codes are unique and safe for Telegram deep-link parameters.
- [ ] Duplicate code collisions are retried without losing the original request.
- [ ] Unsupported messages receive a clear response and are not persisted.
- [ ] Service and repository behavior have focused tests.

## Verification

```bash
uv run ruff check .
uv run pytest tests/content tests/router/admin
```

## PR

Suggested title: `feat(content): add administrator content upload`

Do not implement membership checks, content delivery, statistics, or a web
admin panel in this PR.
