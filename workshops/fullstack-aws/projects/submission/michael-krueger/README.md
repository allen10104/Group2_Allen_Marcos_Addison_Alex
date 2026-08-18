# Notice Board

A full-stack notice board application built for the Full-Stack AWS 10-Aug-2026 cohort.
Users sign up, log in, post notices for everyone to see, react to notices, and can
delete only the notices they posted themselves.

## What makes this different from the base assignment

The scaffolded assignment specs a single Lambda handler, API Gateway, and PostgreSQL
on EC2, with no authentication. This submission takes a different, more production-style
approach, confirmed with the instructor before deployment:

| Area | Assignment scaffold | This submission |
|---|---|---|
| Backend | Single `lambda_function.py` | FastAPI app with `models/` `services/` `controllers/` layering |
| Database | PostgreSQL on EC2 | Supabase (hosted PostgreSQL) |
| Auth | None | JWT-based signup/login, bcrypt password hashing |
| Notice ownership | Anyone can delete any notice | Only the original poster can delete their own notice |
| Compute | Lambda | EC2 (systemd + nginx + HTTPS) |

## Features

- **Public board**: anyone can view all notices without an account (`GET /notices`)
- **Accounts**: sign up and log in with a username and password
- **Post notices**: logged-in users can post a notice with a name and message
- **Delete your own notices**: only the user who posted a notice can delete it,
  enforced server-side, not just hidden in the UI
- **Reactions (USP feature)**: any logged-in user can react to any notice with
  like, heart, or laugh. Each reaction type is independently toggleable, a user
  can have multiple reaction types active on the same notice at once, and
  reaction counts are visible to everyone, including logged-out visitors

## Why authentication and reactions

The base assignment leaves the board fully open: anyone can post or delete anything.
Two additions were made as this submission's USP:

1. **JWT authentication with ownership-based delete.** Signing up issues no special
   privileges beyond identifying who posted what. The board itself stays public to
   view, but posting requires an account, and deleting requires being the original
   poster, verified server-side on every request, not assumed from the UI.
2. **Reactions.** Once accounts exist, they're used for something more than gating
   posts: reacting to notices. This demonstrates the auth system doing real,
   per-user work beyond a single yes/no gate.

## Tech stack

**Backend**
- FastAPI (Python), organized as models / services / controllers
- Supabase (hosted PostgreSQL), accessed via the `supabase-py` client using the
  `service_role` key
- JWT auth (python-jose), bcrypt password hashing
- Deployed to EC2 behind nginx, with HTTPS via Let's Encrypt

**Frontend**
- React + Vite
- Material-UI
- React Router, with a `ProtectedRoute` gating the board behind login
- Axios with a request interceptor that auto-attaches the JWT

## API reference

| Method | Path | Auth required | Description |
|--------|------|:---:|-------------|
| GET | `/health` | No | Health check |
| POST | `/auth/signup` | No | Create an account: `{ username, password }` |
| POST | `/auth/login` | No | Log in: `{ username, password }`, returns a JWT |
| GET | `/notices` | No | List all notices, newest first, with reaction counts |
| POST | `/notices` | Yes | Create a notice: `{ name, message }` |
| DELETE | `/notices/{id}` | Yes | Delete a notice. 403 if you're not the owner |
| POST | `/notices/{id}/reactions` | Yes | Toggle a reaction: `{ reaction_type }`, one of `like`/`heart`/`laugh` |

## Running locally

**Backend**

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate    # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env      # then fill in SUPABASE_URL, SUPABASE_KEY, JWT_SECRET
uvicorn app.main:app --reload --port 8001
```

Run `schema.sql` in your Supabase project's SQL Editor before starting the server,
it creates the `users`, `notices`, and `notice_reactions` tables along with the
required RLS policies and grants.

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env      # set VITE_API_URL to your backend's URL
npm run dev
```

## Testing

A Postman collection (`Notice Board.postman_collection.json`) covers the full flow:
health check, signup, login (including a wrong-password case), the public board view,
creating and deleting notices with and without a token, and a two-account test proving
a user cannot delete another user's notice.
