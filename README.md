# Dano Bot

Modular Telegram bot template built with aiogram, uv, pydantic-settings, SQLModel, and Docker.

This repository intentionally contains the application skeleton and a small `/start` plus `/admin`
example. Product features such as content management, deep links, membership checks, and the admin
panel are follow-up work.

## Requirements

- Python 3.13+
- uv
- Docker Compose (optional)

## Local development

```bash
uv sync
cp .env.example .env
uv run ruff check .
uv run pytest
uv run python -m app.main
```

`BOT_TOKEN`, `ADMIN_IDS`, `DATABASE_URL`, and `REQUIRED_CHANNEL_ID` are loaded through
`pydantic-settings`. Never commit `.env`.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The SQLite data directory is stored in the `bot-data` named volume.

## Structure

```text
app/
├── main.py
├── config.py
├── database/
├── router/
│   ├── admin/
│   └── user/
└── services/
```

Each router owns its handlers and filters. Business logic belongs in application services, while
database access belongs in a future repository layer.

## Scope

The template is the foundation for incremental development. Add one feature module at a time,
with focused tests and a separate pull request when the change is independently reviewable.

