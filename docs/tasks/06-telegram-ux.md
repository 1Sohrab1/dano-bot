# Stage 06: Telegram UX and Interaction System

Status: In Progress

## PR 1: UX Foundation (implemented)

The first reviewable part covers only the interaction foundation:

* Persian-first `/start` welcome with a help button (deep-link delivery unchanged)
* `/admin` dashboard exposing only supported actions (upload, manage, help)
* structured callback data (`UserNav` / `AdminNav`) with back navigation
* upload entry guidance reusing the existing upload workflow
* concise Persian help flows for users and administrators

Deferred to later Stage 06 PRs: interactive content listing, content detail
screens, activation/deactivation/delete/expiration UX flows, and the
membership recovery flow.

## Objective

Transform Dano Bot from a command-oriented interface into a Telegram-native interaction system that is simple, discoverable, and comfortable for both users and administrators.

The existing business logic, services, authorization rules, database models, and content lifecycle remain the source of truth.

This stage focuses on how users interact with those capabilities.

## Problem

The current bot exposes several administrative capabilities primarily through commands:

* `/admin`
* `/list`
* `/activate <code>`
* `/deactivate <code>`
* `/delete <code>`
* `/expire <code> <days>`

While functional, this requires administrators to remember command names, argument formats, and content codes.

The user experience should instead prioritize:

* discoverability
* clear navigation
* minimal cognitive load
* Telegram-native interactions
* consistent button labels
* safe destructive actions
* understandable errors and empty states

## UX Principles

### 1. Buttons before commands

Where an action can be reasonably represented through an inline or reply keyboard, users should not be required to remember command syntax.

Commands may remain available as shortcuts or compatibility interfaces where useful.

### 2. One clear primary action

Each screen or message should make the next likely action obvious.

Avoid presenting too many unrelated actions at once.

### 3. Progressive disclosure

Do not expose every management action immediately.

The interaction flow should progressively move from:

```text
Dashboard
    ↓
Content list
    ↓
Content details
    ↓
Specific action
    ↓
Confirmation
```

### 4. Consistent navigation

Every navigable flow should provide a predictable way to:

* go back
* cancel an operation
* return to the appropriate parent screen

### 5. Safe destructive actions

Destructive operations must require explicit confirmation.

This applies at minimum to:

* deleting content

### 6. Clear state communication

The bot should clearly communicate:

* active vs inactive content
* expiration status
* successful operations
* failed operations
* empty states

### 7. Telegram-native design

The interface should use interaction patterns appropriate for Telegram:

* inline keyboards
* callback queries
* concise messages
* contextual actions
* message editing where appropriate

The bot should not attempt to imitate a web application inside chat.

### 8. Persian-first user experience

The primary interaction language is Persian.

Messages and button labels should be:

* concise
* natural
* consistent
* understandable by non-technical users

## User Experience

### Start

When a user sends `/start` without a deep link:

```text
سلام 👋

به دانو بات خوش اومدی 🎓

از طریق این ربات می‌تونی به محتوای آموزشی دانو دسترسی داشته باشی.
```

The initial experience should not overwhelm the user with unnecessary actions.

Potential navigation actions may include:

* راهنما
* درباره دانو

### Deep Link Flow

The existing deep-link mechanism remains unchanged.

The flow is:

```text
Deep Link
    ↓
Validate content code
    ↓
Check content state
    ↓
Check expiration
    ↓
Check channel membership
    ↓
Deliver content
```

If channel membership is required, the user experience should provide a clear recovery path rather than only displaying an error.

The intended interaction is:

```text
برای دریافت این محتوا ابتدا باید عضو کانال شوید.

[ عضویت در کانال ]

[ بررسی عضویت ]
```

After the user joins the channel, they should be able to retry the delivery flow without manually restarting the entire process.

## Administrator Experience

### Admin Entry Point

The `/admin` command becomes the entry point to the administration interface.

Instead of only confirming administrator status, it should present an administrative dashboard.

Example:

```text
🎛 پنل مدیریت دانو

مدیریت محتوای آموزشی و فایل‌های ربات
```

Actions:

```text
[ 📤 افزودن محتوا ]

[ 📚 مدیریت محتوا ]
```

Future capabilities such as analytics must not be presented until implemented.

## Content Upload

The existing behavior of sending supported content directly to the bot remains supported.

The upload flow should remain simple:

```text
Admin sends content
        ↓
Content is stored
        ↓
Bot confirms success
        ↓
Bot provides access link
```

The success response should clearly distinguish between:

* successful storage
* the generated access link

## Content Management

Content management should no longer require administrators to remember management commands.

The intended flow is:

```text
📚 مدیریت محتوا
        ↓
Content list
        ↓
Select content
        ↓
Content details
        ↓
Choose action
```

### Content List

The list should support pagination.

Each item should allow the administrator to select it for additional details.

The list should communicate:

* content code
* content type
* active/inactive state
* expiration status

### Content Details

A selected content item should display its relevant information.

Example:

```text
📄 اطلاعات محتوا

کد: ABC123
نوع: document
وضعیت: فعال
انقضا: بدون انقضا
```

Available actions should depend on the current state.

For active content:

```text
[ ⛔ غیرفعال کردن ]

[ 🗓 تنظیم انقضا ]

[ 🗑 حذف محتوا ]

[ ← بازگشت ]
```

For inactive content:

```text
[ ✅ فعال کردن ]

[ 🗓 تنظیم انقضا ]

[ 🗑 حذف محتوا ]

[ ← بازگشت ]
```

## Expiration Flow

Expiration currently requires command arguments.

The new interaction should guide the administrator through the operation.

The flow should allow:

* setting a number of days
* removing expiration
* cancelling the operation

The exact input mechanism may use Telegram message input where numeric input is required.

Example:

```text
🗓 تنظیم انقضا

تعداد روزهای اعتبار را ارسال کنید.

برای حذف انقضا:
[ بدون انقضا ]

[ لغو ]
```

## Confirmation Flow

Destructive operations must display a confirmation step.

Example:

```text
⚠️ حذف محتوا

این عملیات غیرقابل بازگشت است.

آیا مطمئن هستید؟
```

Actions:

```text
[ 🗑 بله، حذف کن ]

[ لغو ]
```

Successful operations should replace or update the interaction message where practical to avoid leaving outdated buttons visible.

## Navigation Rules

Navigation must follow a predictable hierarchy.

```text
Admin Dashboard
    ↓
Content Management
    ↓
Content List
    ↓
Content Details
    ↓
Action
```

Back navigation should return to the previous logical level.

Cancellation should return the user to a safe state.

The bot should avoid dead-end interactions.

## Button Conventions

Buttons should use consistent labels.

### Navigation

* ← بازگشت
* لغو

### Primary Actions

* افزودن محتوا
* مدیریت محتوا
* مشاهده جزئیات
* تأیید

### State Changes

* فعال کردن
* غیرفعال کردن

### Destructive Actions

* حذف محتوا
* بله، حذف کن

Destructive actions should be visually and linguistically explicit.

## Error States

Error messages should explain what happened and, where possible, what the user can do next.

Examples include:

* content not found
* invalid content code
* expired content
* inactive content
* membership required
* invalid expiration value

Errors should avoid exposing internal implementation details.

## Empty States

The bot should explicitly handle cases where no content exists.

Example:

```text
📭 محتوایی برای نمایش وجود ندارد.

[ ← بازگشت ]
```

An empty state should not appear as a broken or silent interaction.

## Architecture Constraints

This stage must not rewrite:

* database models
* repository interfaces
* service-layer business logic
* authorization architecture
* deep-link generation

The implementation should primarily extend:

```text
app/router/
    admin/
        keyboards.py
        callbacks.py
        handlers.py
    user/
        keyboards.py
        callbacks.py
        handlers.py
```

Existing router structure may be extended where necessary, but interaction code must remain separated from business logic.

## Backwards Compatibility

Existing commands may remain functional during the transition.

The primary user experience, however, should guide administrators toward the button-based interface.

Command removal is out of scope for this stage unless explicitly decided later.

## Scope

This stage includes:

* UX principles and interaction conventions
* admin dashboard
* button-based content navigation
* content detail screens
* activation and deactivation flows
* deletion confirmation
* expiration interaction flow
* improved membership recovery flow
* navigation and cancellation behavior
* error states
* empty states

## Out of Scope

This stage does not include:

* analytics dashboard
* content search
* categories or folders
* user profiles
* payment systems
* web interface
* mobile application
* redesigning database architecture
* changing the content delivery business rules

## Acceptance Criteria

The stage is complete when:

* administrators can discover primary management actions without memorizing commands
* `/admin` opens an administrative dashboard
* administrators can navigate to content management using buttons
* administrators can browse paginated content
* administrators can select content and view its details
* administrators can activate or deactivate content through the interface
* deleting content requires explicit confirmation
* expiration can be configured without remembering command syntax
* users who need channel membership receive a clear recovery path
* empty states are handled explicitly
* navigation and cancellation do not leave users in dead-end states
* existing service-layer business logic remains intact
* existing tests continue to pass
* new interaction flows are covered by tests

