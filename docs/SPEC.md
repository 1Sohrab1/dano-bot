# Dano Bot Specification

## Objective

Dano Bot is a modular Telegram content-distribution bot. An administrator will
eventually upload content, generate an access link, enforce access requirements,
and deliver the content to users.

The repository currently provides the maintainable starter template only. The
feature work described below is intentionally split into independent pull
requests; this document is the source of truth for that roadmap.

## Current scope

The current template includes:

- aiogram dispatcher with separate `admin` and `user` routers
- `pydantic-settings` configuration loaded from environment variables
- asynchronous SQLModel/SQLite bootstrap
- persistent `User` and `Admin` records keyed by unique Telegram IDs
- idempotent administrator seeding from `ADMIN_IDS` at startup
- centralized admin authorization through `AdminFilter` and `admin_service`
- content metadata persistence (`Content`) with unique deep-link codes
- administrator upload of supported Telegram messages through the admin router
- deep-link delivery of stored content through `/start <code>`
- membership enforcement through an application service when `REQUIRED_CHANNEL_ID`
  is set
- administrator content-management workflows: bounded pagination, inline
  confirmation of activate/deactivate/delete, and relative-day expiration
  management, authorized through `AdminFilter` and `AdminCallbackQueryFilter`
- uv dependency and lockfile management
- Docker and Compose deployment skeleton
- basic `/start` and `/admin` example handlers
- pytest and Ruff verification

The current template does not implement rate limiting or a complete admin panel.

User identity stores only an internal id and `telegram_id`. After seeding,
authorization looks up the `Admin` table rather than reading `ADMIN_IDS` in
handlers. `ADMIN_IDS` remains the bootstrap source of truth.

## Capability map

| Module | Responsibility | Depends on |
|---|---|---|
| foundation | Runtime, configuration, logging, dependency boundaries | — |
| identity | Persistent users and administrators | foundation |
| content | Content metadata and administrator upload workflow | identity |
| access | Deep-link resolution, expiration, active state, and membership checks | content, identity |
| administration | Admin-panel workflows and content management | identity, content |
| operations | Migrations, observability, deployment, and recovery | foundation, identity, content |

Build order:

`foundation → identity → content → access → administration → operations`

Each capability is implemented as one or more focused PRs from
`docs/tasks/`. A later capability must not bypass the contracts of its
dependencies.

## Users and roles

### User

- starts the bot
- opens a content deep link
- completes configured access requirements
- receives permitted content

### Administrator

- uploads supported Telegram content
- receives a unique access link
- manages content state and expiration
- uses future administration workflows

Administrator authorization must be centralized and must never be duplicated
inside individual handlers. Admin routes use `AdminFilter`, which delegates to
`admin_service.is_admin`.

## Core flows

### Content delivery

```text
/start <content_code>
        |
        v
resolve content -> validate active/expiration -> validate membership
        |                                      |
        +-- invalid/blocked ------------------+--> safe user message
        |
        v
deliver source message
```

### Architecture boundary

```text
Telegram update
      |
      v
Router/handler -> application service -> repository -> SQLModel database
                         |
                         +-> Telegram API boundary services
```

Handlers must remain thin. Business rules belong in services, persistence
belongs in repositories, and configuration belongs in `Settings`.

## Technology stack

- Python 3.13+
- aiogram
- uv and `uv.lock`
- pydantic-settings
- SQLModel with SQLAlchemy async engine
- SQLite for the initial deployment; PostgreSQL compatibility is a requirement
- pytest and Ruff
- Docker Compose

## Configuration

Required environment values are documented in `.env.example`:

- `BOT_TOKEN`
- `ADMIN_IDS`
- `DATABASE_URL`
- `REQUIRED_CHANNEL_ID` (optional; when unset or blank, membership is not
  enforced and delivery is not gated)
- `DEBUG`

Secrets must remain outside version control. Configuration changes require an
update to `.env.example` and the relevant documentation.

## Project structure

```text
app/
├── main.py
├── config.py
├── database/
├── router/
│   ├── admin/
│   └── user/
├── services/
└── ...
docs/
├── SPEC.md
└── tasks/
tests/
├── conftest.py
└── test_*.py
```

New feature modules should use a directory, not a growing catch-all module.
Each router directory owns its handlers, filters, and middleware. Shared
infrastructure must not contain feature-specific policy.

## Commands

```bash
uv sync
uv run ruff check .
uv run pytest
uv run python -m compileall -q app
uv run python -m app.main
docker compose up --build
```

## Testing strategy

- Unit tests for pure services, validators, code generation, and policies.
- Repository tests against an isolated SQLite database.
- Router tests for authorization and update-to-response behavior.
- A small number of Telegram API boundary tests using explicit fakes.
- Docker and Compose validation for deployment changes.

Every behavior-changing PR must add or update focused tests. Tests must verify
observable outcomes rather than private implementation details.

## Boundaries

### Always

- Keep handlers thin and modules bounded.
- Validate external input at boundaries.
- Run Ruff and pytest before committing.
- Update this spec or the relevant task when a contract changes.
- Keep secrets and runtime database files out of Git.

### Ask first

- Changing the database schema or migration strategy.
- Adding a production dependency or external service.
- Changing authorization semantics.
- Changing CI, deployment, or public Telegram behavior.

### Never

- Implement the entire product in one PR.
- Put database queries or business rules directly in handlers.
- Commit `.env`, tokens, user data, or generated runtime databases.
- silently weaken authorization or membership checks.

## Definition of done for each PR

- Scope maps to one task in `docs/tasks/`.
- Acceptance criteria are checked by tests or a documented manual verification.
- Ruff, pytest, and relevant build/deployment checks pass.
- Documentation and `.env.example` are updated when needed.
- The PR is small enough to review and can be reverted independently.

## Long-term success criteria

- Users can securely receive valid, permitted content through deep links.
- Administrators can manage content without direct database access.
- New features can be added as bounded modules without expanding monolithic
  router or service files.
- SQLite-to-PostgreSQL migration does not require rewriting handlers or
  application services.
- Deployment is reproducible through uv and Docker.

## Open decisions

- PostgreSQL migration timing and Alembic rollout.
- Admin panel transport: Telegram-only first or a separate web application.
- Rate-limit storage and strategy for multi-instance deployment.

Supported Telegram content types for administrator upload are document, video,
photo, audio, voice, animation, and video note. Other message types are rejected
and are not persisted. Delivery of stored source messages is Stage 03.
