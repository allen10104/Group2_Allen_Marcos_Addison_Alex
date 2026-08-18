# SyncUp — The Notice Ledger

🔗 **Live app:** [https://d29oqtt6m1oqoi.cloudfront.net](https://d29oqtt6m1oqoi.cloudfront.net) — see [Sample login](#sample-login) below for credentials.

An internal company notice board. Managers post notices and provision accounts; employees read notices and submit their own (pending approval). Built as a from-scratch parallel to a prior "bank app" project, reusing the same layered architecture and JWT/RBAC pattern but swapping PostgreSQL for MongoDB.

## The three differentiators

1. **Manager-provisioned accounts** — no public signup for the base case; a manager creates employee accounts directly. (Self-registration was added later — see "Registration & invite codes" below — but manager accounts specifically still require verification before they're usable.)
2. **Approval workflow** — an employee's notice sits `PENDING` until a manager approves or rejects it. A manager's own notice goes live instantly.
3. **Read-receipt tracking** — every notice tracks exactly which employees have acknowledged it ("9 of 14 read"), with a per-notice breakdown of who's read it and who hasn't.

## Architecture

```
HTTP request
  → controllers/   routes, status codes, RBAC gates
  → services/      business logic (approval rules, read tracking, invite-code validation)
  → data/          MongoDB queries (via Motor)
  → security/      passwords (bcrypt), JWT (PyJWT), role dependencies
```

| Layer            | Tech                                                                              |
| ---------------- | --------------------------------------------------------------------------------- |
| Backend          | FastAPI + Uvicorn                                                                 |
| Database         | MongoDB (Atlas), via Motor (async driver)                                         |
| Auth             | bcrypt password hashing + PyJWT access/refresh tokens                             |
| RBAC             | `require_roles(...)` FastAPI dependency, roles: `MANAGER`, `EMPLOYEE`             |
| Frontend         | React + Vite + MUI (Material UI), themed for a macOS-style look                   |
| Frontend state   | React Context (`AuthContext`) + JWT decoded client-side, tokens in `localStorage` |
| Frontend routing | React Router, with `ProtectedRoute` gating by login state and role                |

Mongo is document-based, not relational — a few real adaptations from a SQL design:

- No `RETURNING *`; inserts return an id, so create functions build the full object in Python instead of re-querying.
- Read receipts are embedded directly inside each notice document (`notice.read_by: [{user_id, read_at}, ...]`) rather than a separate join table — avoids a join for the single most common read-tracking query.
- Approve/reject and single-use invite-code redemption both use an atomic filter+update (e.g. `{"status": "PENDING"}` as part of the update filter, not a separate read-then-write) to avoid race conditions like double-approval.

## The flow

**Bootstrapping the first account.** There's no way to get a manager into an empty database through the app itself — `seed_manager.py` is a standalone script (not an API endpoint) that plants the first manager account directly, using `SEED_MANAGER_EMAIL`/`SEED_MANAGER_PASSWORD` from `.env`.

**Getting an account, three ways:**

1. A manager creates an employee directly (`POST /users`) — instantly active, no verification needed.
2. Someone self-registers as an employee (`POST /auth/register`) — instantly active.
3. Someone self-registers as a manager — active immediately **only** if they supply a valid invite code from an existing manager; otherwise the account is created `PENDING` and can't log in until verified.

**Becoming a verified manager without a code up front:** register → account sits `PENDING` → an existing manager generates a code for that specific email (`POST /admin/invite-codes`) → the pending user redeems it (`POST /auth/verify-manager`) → account flips to `APPROVED` → can log in.

**Posting a notice:**

- Employee submits → status `PENDING` → invisible to other employees until a manager acts on it.
- Manager submits → status `APPROVED` immediately → live on the feed right away.
- Manager approves/rejects a pending notice (`POST /notices/{id}/approve` or `/reject`).

**Read tracking:**

- Employee marks a notice read (`POST /notices/{id}/ack`) → idempotent, appends a `{user_id, read_at}` receipt.
- Manager views the read report (`GET /notices/{id}/read-status`) → cross-references the notice's readers against the full employee roster to show who has and hasn't read it.

## Features

- Login / self-registration (employee or manager) / manager-invite-code verification
- Notice feed (role-filtered: employees only ever see `APPROVED` notices)
- Submit a notice (approval requirement depends on role)
- Approval queue (manager-only) — approve/reject pending notices
- Read-tracking: unread indicator (dot), "mark as read," muted/read card styling, per-notice read report with progress bar
- Add employee directly (manager-only)
- Generate invite codes for new managers (manager-only)

## API reference

| Method | Path                        | Access                                  |
| ------ | --------------------------- | --------------------------------------- |
| POST   | `/auth/login`               | public                                  |
| POST   | `/auth/refresh`             | public (requires a valid refresh token) |
| POST   | `/auth/register`            | public                                  |
| POST   | `/auth/verify-manager`      | public                                  |
| GET    | `/auth/me`                  | any logged-in user                      |
| POST   | `/users`                    | manager only                            |
| GET    | `/notices`                  | any logged-in user                      |
| POST   | `/notices`                  | any logged-in user                      |
| POST   | `/notices/{id}/approve`     | manager only                            |
| POST   | `/notices/{id}/reject`      | manager only                            |
| POST   | `/notices/{id}/ack`         | employee only                           |
| GET    | `/notices/{id}/read-status` | manager only                            |
| POST   | `/admin/invite-codes`       | manager only                            |

## Sample login

A manager account already exists in the shared dev database, created and verified through the real registration + invite-code flow (not a shortcut):

```
email:    smoke-newmanager@example.com
password: password123
```

_Last deployed via GitHub Actions._

## Deployment architecture

The live frontend (CloudFront + S3) talks to a **Lambda + API Gateway** backend as of the latest deploy. An EC2 instance running the same backend (via systemd) is kept running and kept in sync by the same CI workflow, as a fallback - both are updated on every push, only the frontend's `VITE_API_URL` decides which one is actually "live."
