# Implementation Tasks

Each file in this directory defines one independently reviewable stage. The
intended workflow is one branch and one pull request per stage, in dependency
order.

## Sequence

| Stage | Task | Status | Depends on |
|---|---|---|---|
| 00 | [Starter template](./00-foundation-template.md) | Done | — |
| 01 | [Identity and authorization](./01-identity.md) | Done | 00 |
| 02 | [Content persistence and upload](./02-content.md) | Planned | 01 |
| 03 | [Access and delivery](./03-access.md) | Planned | 02 |
| 04 | [Administration workflows](./04-administration.md) | Planned | 01, 02 |
| 05 | [Operations and production readiness](./05-operations.md) | Planned | 01–04 |

## PR rules

Every stage PR must:

1. Link its task document in the PR description.
2. Keep the scope limited to that stage.
3. Include focused tests for changed behavior.
4. Run `uv run ruff check .` and `uv run pytest`.
5. Update `docs/SPEC.md` when a contract or decision changes.
6. Record intentionally deferred work in the PR description or the next task.

Do not combine multiple planned stages into one PR. A stage may be split into
smaller PRs only when the task document is updated first.
