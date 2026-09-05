# Stage 04: Administration Workflows

Status: Done

## Objective

Add Telegram-based administration workflows for managing stored content without
coupling management policy to the router or database layer.

## Dependencies

- Stage 01
- Stage 02

## Scope

- Add separate admin subrouters for content management commands.
- List content with bounded pagination.
- Activate, deactivate, and delete content with explicit confirmation.
- Add expiration management.
- Record administrator actions in structured logs.
- Add authorization and state-transition tests.

## Acceptance criteria

- [x] Every admin command passes centralized authorization.
- [x] Content lists are bounded and stable under pagination.
- [x] Destructive actions require explicit confirmation and are auditable.
- [x] Invalid state transitions return safe, useful responses.
- [x] Admin handlers remain thin and delegate to application services.

## Verification

```bash
uv run ruff check .
uv run pytest tests/administration tests/router/admin
```

## PR

Suggested title: `feat(admin): add content management workflows`

This stage is Telegram administration only. A web admin panel is a separate
design decision and must not be introduced implicitly.
