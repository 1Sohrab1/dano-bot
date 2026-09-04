FROM ghcr.io/astral-sh/uv:0.12.9 AS uv
FROM python:3.13-slim-bookworm

COPY --from=uv /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev

COPY app ./app

RUN mkdir -p /app/data && \
    useradd --create-home --uid 10001 bot && \
    chown -R bot:bot /app
USER bot

CMD ["uv", "run", "--no-dev", "python", "-m", "app.main"]
