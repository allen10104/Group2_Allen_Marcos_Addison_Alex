# Notice Board

A full-stack notice board: post short messages to a shared board, edit or
delete your own, and — if you're an admin — pin the important ones to the
top and moderate anyone's post. The UI renders the board as an actual
corkboard, with each notice drawn as a sticky note.

This document describes what the application actually does and how it's
put together. For the assignment brief itself (the AWS deployment tiers
this project is graded against), see [ASSIGNMENT.md](./ASSIGNMENT.md).

---

## What was built

The assignment ships with a working app and asks students to focus only on
deployment (Tiers 1–4 in `ASSIGNMENT.md`). On top of that baseline, this
submission also extended the application itself:

**Core (as provided by the assignment):**
- Register / log in with a username and password, get back a JWT
- Post a notice while logged in
- View all notices, publicly, without logging in
- Delete a notice you posted

**Added on top of the baseline:**
- **Email at registration** — sign-up now collects and validates an email
  address (server-side, via Pydantic's `EmailStr`) alongside the username
  and password
- **Edit your own notices** — a notice can be corrected after posting
  instead of only delete-and-repost; edited notices are marked "(edited)"
  with a timestamp
- **Admin role** — usernames listed in the `ADMIN_USERNAMES` environment
  variable get elevated permissions: they can edit or delete *any* notice,
  not just their own
- **Pin as important** — admins can pin a notice; pinned notices always
  sort to the top of the board, ahead of newer posts, until unpinned
- **Corkboard UI redesign** — the board is a textured cork background;
  each notice is a rotated, colored sticky note with a pinned tack or
  tape strip, a handwritten font, and a torn-corner delete control;
  pinned notices get a red tack, a glowing highlight, and an "Important"
  ribbon so they don't blend in with the rest of the board

---

## Architecture

```
                         ┌─────────────────────────┐
                         │      React Frontend      │
                         │   (Vite, plain fetch)    │
                         └────────────┬─────────────┘
                                      │ HTTPS / JSON
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI app         │
                         │  (app.py + notice_board)  │
                         │                            │
                         │  local dev: uvicorn        │
                         │  prod: Lambda via Mangum,  │
                         │  fronted by API Gateway    │
                         └────────────┬─────────────┘
                                      │ psycopg2
                                      ▼
                         ┌─────────────────────────┐
                         │       PostgreSQL           │
                         │  local dev: Windows service │
                         │  prod: EC2 instance          │
                         └─────────────────────────┘
```

The same FastAPI code runs two ways without any changes: directly under
`uvicorn` for local development, or wrapped by `Mangum` as a Lambda
handler in production (`handler = Mangum(app, lifespan="off")` in
`backend/app.py`). API Gateway is configured to proxy every path straight
through to the Lambda, so FastAPI's own router handles all path matching
in both environments.

---

## Data model

Two tables, created automatically on first request (`ensure_tables()` in
`backend/notice_board/database.py`) and migrated in place with
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` if columns were added after a
database already existed:

**`users`**

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `username` | `TEXT UNIQUE NOT NULL` | login identifier |
| `email` | `TEXT` | collected at registration, not currently unique/verified |
| `password_hash` | `TEXT NOT NULL` | bcrypt hash, never the raw password |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |

**`notices`**

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `message` | `TEXT NOT NULL` | |
| `author` | `TEXT` | username of the poster |
| `pinned` | `BOOLEAN NOT NULL DEFAULT FALSE` | admin-controlled "important" flag |
| `created_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `updated_at` | `TIMESTAMPTZ` | set on edit, `NULL` if never edited |

---

## Authentication & permissions

Login and registration both return a JWT (`HS256`, signed with the
`JWT_SECRET` env var, default 60-minute expiry via `JWT_EXPIRE_MINUTES`).
The token payload carries everything a protected route needs to know
about the caller, so no extra database lookup is required per request:

```json
{
  "sub": "alice",
  "is_admin": false,
  "iat": 1699999999,
  "exp": 1700003599
}
```

`is_admin` is computed once, at the moment the token is issued, by
checking the username against the comma-separated `ADMIN_USERNAMES`
environment variable (`backend/notice_board/config.py`). There is no
`is_admin` column in the database — admin status is a deployment-time
configuration, not stored per-user state. To make a user an admin, add
their username to `ADMIN_USERNAMES` and have them log in again (an
already-issued token won't retroactively gain the claim).

Permission rules, enforced in `backend/notice_board/routers/notices.py`:

| Action | Who can do it |
|---|---|
| View notices | anyone, no login required |
| Post a notice | any logged-in user |
| Edit a notice | the note's author, or an admin |
| Delete a notice | the note's author, or an admin |
| Pin / unpin a notice | admins only |

---

## Notice lifecycle & ordering

`GET /notices` sorts with `ORDER BY pinned DESC, created_at DESC` — every
pinned note sorts ahead of every unpinned note, and within each group the
newest comes first. This is done in the database query, not client-side,
so pin order is consistent no matter which client reads it. The frontend
mirrors the same sort locally after a pin/unpin action so the moved note
doesn't wait on a full page reload to jump into place.

---

## Project structure

```
notice-board/
├── backend/
│   ├── app.py                        # FastAPI app assembly + Mangum Lambda handler (entrypoint)
│   ├── build.py                      # Packages app.py + notice_board/ into lambda.zip
│   ├── requirements.txt
│   └── notice_board/
│       ├── config.py                 # Env var configuration (JWT_SECRET, ADMIN_USERNAMES, ...)
│       ├── database.py               # get_connection() + ensure_tables() (schema + migrations)
│       ├── security.py               # Password hashing, JWT issue/verify, get_current_user dependency
│       ├── schemas.py                # Pydantic request/response models
│       └── routers/
│           ├── auth.py               # POST /auth/register, POST /auth/login
│           └── notices.py            # /notices CRUD + /notices/{id}/pin
│
├── frontend/
│   └── src/
│       ├── main.jsx                  # React entrypoint
│       ├── App.jsx                   # Top-level state & data flow (auth, notice list, edit state)
│       ├── api.js                    # All backend HTTP calls; decodes JWT client-side for display
│       ├── index.css                 # Corkboard background + sticky-note styling
│       ├── components/
│       │   ├── LoginForm.jsx         # Combined login/register screen
│       │   ├── Composer.jsx          # "Write a notice" sticky-note form
│       │   └── NoteCard.jsx          # A single sticky note: view/edit modes + actions
│       └── utils/
│           └── noteVisuals.js        # Deterministic per-note color/rotation/fastener
│
└── terraform/                        # AWS infrastructure (Tiers 1–4, see ASSIGNMENT.md)
```

---

## API reference

All request/response bodies are JSON. Protected routes require
`Authorization: Bearer <token>`.

| Method | Path | Auth | Body | Description |
|---|---|---|---|---|
| POST | `/auth/register` | — | `{username, email, password}` | Create an account, returns `{access_token, token_type}` |
| POST | `/auth/login` | — | `{username, password}` | Returns `{access_token, token_type}` |
| GET | `/notices` | — | — | List all notices, pinned first, newest first |
| POST | `/notices` | required | `{message}` | Create a notice as the caller |
| PUT | `/notices/{id}` | required | `{message}` | Edit a notice (author or admin only) |
| PATCH | `/notices/{id}/pin` | required | `{pinned}` | Pin/unpin a notice (admin only) |
| DELETE | `/notices/{id}` | required | — | Delete a notice (author or admin only) |

A notice object looks like:

```json
{
  "id": 5,
  "message": "hello board",
  "author": "alice",
  "pinned": false,
  "created_at": "2026-08-16T12:02:10.782878-04:00",
  "updated_at": null
}
```

---

## Running locally

Requires PostgreSQL reachable from your machine (a local install works
fine for development — see `BUILD_GUIDE.md` for a from-scratch walkthrough).

**Backend:**

```powershell
cd notice-board/backend
.\venv\Scripts\Activate.ps1

$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_DB="notice_board"
$env:PG_USER="nb_user"
$env:PG_PASSWORD="localdevpass"
$env:JWT_SECRET="dev-only-secret-change-me"
$env:ADMIN_USERNAMES="admin"      # optional: comma-separated list of admin usernames

uvicorn app:app --reload --port 8000
```

**Frontend:**

```bash
cd notice-board/frontend
npm install
npm run dev
```

Set `frontend/.env.local` to point at the backend:

```
VITE_API_URL=http://localhost:8000
```

Then open `http://localhost:5173`.

---

## Deployment status

This project has **not yet been deployed to AWS**. Everything above has
been built and verified running locally only. To deploy per
`ASSIGNMENT.md`'s Tier 1:

1. Provision an EC2 instance running PostgreSQL (the assignment's
   prerequisite lab) — not yet done for this project.
2. Add `admin_usernames` as a Terraform variable and pass it through as
   a Lambda environment variable in `terraform/main.tf`, the same way
   `jwt_secret` is wired today — the admin/pin feature depends on it and
   it is currently only set locally, not in Terraform.
3. Run `python build.py` to produce `backend/lambda.zip` (this now
   bundles the `notice_board` package alongside `app.py` — see
   `backend/build.py`).
4. `terraform init && terraform apply`.
5. Build the frontend with `VITE_API_URL` set to the deployed API
   Gateway URL, and upload it to the S3 bucket Terraform creates.

---

## Known limitations

- Email addresses are collected and validated for format, but **not**
  checked for uniqueness or verified via a confirmation email.
- Admin status lives in an env var, not the database — revoking or
  granting admin requires a redeploy (or restart, locally) and affects
  only tokens issued afterward.
- Local Postgres, when set up via the winget installer without admin
  rights to restart the Windows service, may be running with `trust`
  authentication (no password enforced) rather than `scram-sha-256` —
  fine for a local-only dev database, but worth knowing if you go
  looking for it in `pg_hba.conf`.
