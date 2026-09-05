# Backup and Restore

This runbook covers the SQLite deployment described in `compose.yaml`:
application data lives in `/app/data` inside the container, persisted in
the named Docker volume `bot-data`.

## What is (and is not) included

- Included: everything under `/app/data`, i.e. the SQLite database file
  (`dano.db`). This is the only state the bot persists.
- Not included: `.env` (runtime secrets and configuration). Back up `.env`
  separately in a secrets manager; never commit it and never bundle it
  into archives shared with the repository.

## Finding the volume name

Docker prefixes the volume with the Compose project name (by default the
directory name):

```bash
docker volume ls | grep bot-data
docker compose config | grep -A2 volumes
```

The examples below use `dano-bot_bot-data`; replace it with the actual name
printed by the commands above.

## Backup

SQLite is safest to copy while no writer is active, so stop the bot first:

```bash
docker compose stop bot
docker run --rm \
  -v dano-bot_bot-data:/data:ro \
  -v "$(pwd)":/backup \
  alpine tar czf "/backup/bot-data-$(date +%Y%m%d-%H%M%S).tar.gz" -C /data .
docker compose start bot
```

Verify the archive lists the database file:

```bash
tar tzf bot-data-<timestamp>.tar.gz
```

Store the archive off-host. Note the outage window is only the time the
container is stopped.

## Restore

```bash
docker compose stop bot
docker run --rm \
  -v dano-bot_bot-data:/data \
  -v "$(pwd)":/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/bot-data-<timestamp>.tar.gz -C /data"
docker compose start bot
```

Then verify startup and database health:

```bash
docker compose ps
docker compose logs --tail 50 bot
```

Expect, in order: `event=database_migration_started`,
`event=database_migration_completed`, and `event=application_ready`.
If `event=startup_failed` appears instead, the container did not start
correctly; keep it stopped and investigate before retrying.
