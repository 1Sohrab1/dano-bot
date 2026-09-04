# Stage 00: Starter Template

Status: Done

## Goal

Provide a runnable, modular aiogram starter without implementing product
features.

## Delivered

- Separate `admin` and `user` routers.
- Environment configuration with `pydantic-settings`.
- uv dependency and lockfile workflow.
- Async SQLModel/SQLite bootstrap.
- Dockerfile, Compose service, and persistent data volume.
- Basic `/start` and `/admin` examples.
- GitHub issue and pull request templates.

## Verification

- `uv run ruff check .`
- `uv run pytest`
- `uv run python -m compileall -q app`
- `docker compose config -q`
- Docker image build succeeds.

## Explicitly deferred

Content upload, deep links, membership checks, rate limiting, migrations, and
the complete admin panel belong to later stages.
