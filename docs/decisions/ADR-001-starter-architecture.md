# ADR-001: Use a Modular aiogram Starter Architecture

## Status

Accepted

## Date

2026-09-04

## Context

Dano Bot is expected to grow from a small Telegram bot into a content
distribution platform with administrative workflows. A monolithic handler file
would make future features difficult to isolate, test, and review.

The project also needs a reproducible development and deployment path without
moving configuration into source code.

## Decision

- Use aiogram with one dispatcher and separate `admin` and `user` routers.
- Organize router-specific handlers and filters under directories.
- Keep configuration in `pydantic-settings`.
- Manage dependencies and the lockfile with uv.
- Use SQLModel with an async engine behind a database boundary.
- Use SQLite for the initial template and preserve PostgreSQL compatibility as
  a future requirement.
- Package the bot with Docker Compose and persist runtime data through a named
  volume.
- Deliver product capabilities as dependency-ordered, independently reviewable
  pull requests.

## Alternatives considered

### One monolithic router

Rejected because admin and user authorization and workflows would become
coupled as the bot grows.

### Framework-specific database access in handlers

Rejected because it makes business logic difficult to test and complicates the
SQLite-to-PostgreSQL migration.

### Implement the complete product in the starter

Rejected because a large initial change would be difficult to review and would
make architectural boundaries implicit rather than testable.

### Pin all runtime configuration in source code

Rejected because tokens, deployment settings, and environment differences must
remain outside version control.

## Consequences

The initial template has more directories than a single-file bot, but each
future capability has a clear home and can be delivered independently. The
database and Telegram API boundaries must be maintained as the feature set
expands.

The current SQLite bootstrap is intentionally not a complete migration system;
Alembic and PostgreSQL operational work are tracked in Stage 05.
