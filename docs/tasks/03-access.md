# Stage 03: Access and Delivery

Status: Done

## Objective

Resolve a content deep link, validate access policy, and deliver the original
Telegram message to an eligible user.

## Dependencies

- Stage 02

## Scope

- Parse `/start <content_code>` without accepting malformed parameters.
- Reject unknown, inactive, and expired content.
- Add a membership service for the configured required channel.
- Copy the stored source message to the requesting user.
- Handle Telegram API failures without exposing internal details.
- Add structured events for access denied and delivery outcomes.

## Acceptance criteria

- [x] Invalid, inactive, and expired codes produce safe user-facing messages.
- [x] Membership is checked before delivery when a channel is configured.
- [x] A valid eligible request delivers exactly the stored source message.
- [x] Telegram failures are logged with safe context and return a generic message.
- [x] Access policy and delivery behavior are covered by focused tests.

## Verification

```bash
uv run ruff check .
uv run pytest tests/access tests/router/user
```

## PR

Suggested title: `feat(access): deliver content through validated deep links`

Keep membership policy in an application service. Do not put Telegram API calls
or database queries in the handler beyond calling injected services.
