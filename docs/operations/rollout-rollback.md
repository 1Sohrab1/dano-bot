# Rollout and Rollback

## Rollout (deployment)

1. Take a backup first. Follow `backup-restore.md`; a rollout without a
   verified backup is not a rollout, it is a gamble.

2. Obtain the new version:

   ```bash
   git pull
   ```

3. Review configuration. Compare `.env` against `.env.example`; each new
   variable is documented there. Add any missing values to `.env` before
   starting the new version. Never commit `.env`.

4. Build and start the updated container:

   ```bash
   docker compose up --build -d bot
   ```

5. Verify the rollout:

   ```bash
   docker compose ps
   docker compose logs --tail 50 bot
   ```

   Expect `event=database_migration_started`,
   `event=database_migration_completed`, and `event=application_ready`.

### Migration behavior

Database migrations run automatically during application startup
(`alembic upgrade head`). A rollout therefore applies pending schema
migrations exactly once, when the new container first starts. There is
no separate migration step to run.

## Rollback

Decide first whether the database schema changed between the versions.
`git log --oneline -- app/database/migrations/versions/` shows migration
history.

### Application-only rollback (no new migrations applied)

Return to the previously known-good version and restart:

```bash
docker compose down
git checkout <previous-tag-or-commit>
docker compose up --build -d bot
docker compose logs --tail 50 bot
```

Verify `event=application_ready` as in the rollout section.

### Rollback after a migration was applied

Alembic downgrades in this repository are destructive (the initial
migration's downgrade drops tables), so downgrading is not a supported
rollback procedure and must not be run against production data.

The supported procedure is to restore the pre-rollout backup, which
returns both the application data and the schema version together:

1. Check out the previously known-good version (see above) but do not
   start it yet.
2. Follow the restore procedure in `backup-restore.md`.
3. Start the container and verify `event=application_ready`.

### Verification after any rollback

- `docker compose ps` shows the container up.
- Logs contain `event=application_ready` and no `event=startup_failed`.
- Spot-check the bot with `/admin` (as an administrator) and a normal
  `/start` as a user.
