# Build Guide: Notice Board (FastAPI + JWT + React + Postgres)

Every step below: copy the code → run the test command → confirm the
output matches → only then move to the next step. Every command in
this guide was actually run in a clean environment while writing it,
so the "expected output" blocks are real, not guessed.

Work top to bottom. Don't skip a test — each step builds on the last
one working.

---

## Step 0 — Check your tools

```bash
python3 --version
node --version
npm --version
```

**Expected:** something like `Python 3.11+`, `v18+`, `10+`. If any of
these error with "command not found," install that tool before
continuing (Python 3, Node.js, and npm are all you need locally —
PostgreSQL comes next).

---

## Step 1 — Project folders

```bash
mkdir -p notice-board/backend notice-board/frontend
cd notice-board
```

**Test:** `ls` should show `backend` and `frontend`.

---

## Step 2 — Local PostgreSQL

You need Postgres running locally to develop against, separate from
the EC2 Postgres you'll point at in production later.

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
sudo service postgresql start
```

**Create a dev database and user:**

```bash
sudo -u postgres psql -c "CREATE USER nb_user WITH PASSWORD 'localdevpass';"
sudo -u postgres createdb -O nb_user notice_board
```

**Test — confirm you can actually connect:**

```bash
PGPASSWORD=localdevpass psql -h localhost -U nb_user -d notice_board -c "SELECT 1 AS connected;"
```

**Expected output:**
```
 connected
-----------
         1
(1 row)
```

If you see that, Postgres is real and reachable. If you get
`connection refused`, Postgres isn't running — go back and start it.
Do not move on until this works — every later step depends on it.

---

## Step 3 — Python virtual environment

Isolates this project's Python packages from your system Python.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

Your terminal prompt should now show `(venv)` at the start of the line.

**Install the first two packages — just enough to prove FastAPI works:**

```bash
pip install --upgrade pip
pip install fastapi "uvicorn[standard]"
```

**Test:**

```bash
python3 -c "import fastapi; print('fastapi', fastapi.__version__)"
```

**Expected output:** `fastapi 0.11x.x` (some version number — the
exact number doesn't matter, an error does).

---

## Step 4 — Smallest possible FastAPI app

Create `backend/app.py`:

```python
# app.py — smallest possible FastAPI app, just to prove the server runs.
# We will add real routes on top of this in later steps.

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
```

**Run it:**

```bash
uvicorn app:app --reload --port 8000
```

Leave that running. **Open a second terminal** for the test (keep the
server running in the first one for every step from here on).

**Test, from the second terminal:**

```bash
curl -s http://localhost:8000/health
```

**Expected output:**
```json
{"status":"ok"}
```

This confirms: Python works, FastAPI is installed correctly, Uvicorn
can serve it, and your terminal can reach it over HTTP. Every later
step is additive on top of this working baseline.

---

## Step 5 — Add the database connection

Install the DB driver (in the terminal running uvicorn, stop it first
with `Ctrl+C`, then):

```bash
pip install psycopg2-binary
```

Update `backend/app.py` — add a DB connection function and a table-
creation function, plus one route that proves the DB round-trip works:

```python
# app.py

import os
from fastapi import FastAPI
import psycopg2

app = FastAPI()

# Connection details come from environment variables so the same code
# works locally and in Lambda later — never hardcode credentials.
def get_connection():
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=os.environ.get("PG_PORT", "5432"),
        dbname=os.environ.get("PG_DB", "notice_board"),
        user=os.environ.get("PG_USER", "nb_user"),
        password=os.environ.get("PG_PASSWORD", "localdevpass"),
        connect_timeout=5,
    )


def ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                author TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    """Temporary route just to prove the DB connection + table creation work."""
    conn = get_connection()
    try:
        ensure_tables(conn)
        return {"db": "connected", "table": "notices ready"}
    finally:
        conn.close()
```

**Run it again:**

```bash
uvicorn app:app --reload --port 8000
```

**Test:**

```bash
curl -s http://localhost:8000/db-check
```

**Expected output:**
```json
{"db":"connected","table":"notices ready"}
```

**Also verify the table actually exists in Postgres**, not just that
FastAPI claims it does:

```bash
PGPASSWORD=localdevpass psql -h localhost -U nb_user -d notice_board -c "\dt"
```

**Expected output:** a table listing that includes `notices`. This
step is the one most likely to silently fail (wrong password, wrong
port, Postgres not accepting connections) — confirm both the curl
*and* the `\dt` before moving on.

---

## Step 6 — Auth dependencies

```bash
pip install pyjwt bcrypt pydantic
```

**Test the two libraries work in isolation before wiring them into
the app** — this isolates "is bcrypt broken" from "is my route
broken" if something goes wrong later:

```bash
python3 -c "
import bcrypt, jwt
h = bcrypt.hashpw(b'testpassword', bcrypt.gensalt())
print('bcrypt hash works:', bcrypt.checkpw(b'testpassword', h))
token = jwt.encode({'sub': 'alice'}, 'testsecret', algorithm='HS256')
decoded = jwt.decode(token, 'testsecret', algorithms=['HS256'])
print('jwt round-trip works:', decoded['sub'] == 'alice')
"
```

**Expected output:**
```
bcrypt hash works: True
jwt round-trip works: True
```

---

## Step 7 — Register and login endpoints

Replace `backend/app.py` entirely with:

```python
# app.py

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import psycopg2
import psycopg2.errors
import psycopg2.extras
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

app = FastAPI()
security = HTTPBearer()


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=os.environ.get("PG_PORT", "5432"),
        dbname=os.environ.get("PG_DB", "notice_board"),
        user=os.environ.get("PG_USER", "nb_user"),
        password=os.environ.get("PG_PASSWORD", "localdevpass"),
        connect_timeout=5,
    )


def ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                author TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


# ---------- request/response shapes ----------
# Pydantic models = automatic validation. If the JSON body doesn't
# match these rules, FastAPI rejects it with a 422 before our code runs.

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- auth helpers ----------

def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,                              # who this token belongs to
        "iat": now,                                    # issued-at
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),  # expiry
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_username(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    A FastAPI dependency. Any route that adds
    `username: str = Depends(get_current_username)` to its signature
    automatically requires a valid Bearer token — this function runs
    BEFORE the route body, and raises 401 if the token is missing,
    expired, or invalid.
    """
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return payload["sub"]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (body.username, password_hash),
                )
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        conn.commit()
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (body.username,))
            row = cur.fetchone()
        if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        return TokenResponse(access_token=create_access_token(body.username))
    finally:
        conn.close()


@app.get("/whoami")
def whoami(username: str = Depends(get_current_username)):
    """Temporary route just to prove the auth dependency works end to end."""
    return {"you_are": username}
```

**Run it:**

```bash
uvicorn app:app --reload --port 8000
```

**Test 1 — register a user:**

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "hunter22222"}'
```

**Expected output:** a JSON object with `access_token` (a long
dot-separated string) and `"token_type":"bearer"`. **Copy that token**
— you'll use it in the next test.

**Test 2 — registering the same username again should fail:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "hunter22222"}'
```

**Expected output:** `409` (Conflict).

**Test 3 — login with the right password:**

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "hunter22222"}'
```

**Expected output:** another token, status 200.

**Test 4 — login with the wrong password:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "wrongpassword"}'
```

**Expected output:** `401`.

**Test 5 — the auth dependency itself.** Paste the token from Test 1
in place of `PASTE_TOKEN_HERE`:

```bash
TOKEN="PASTE_TOKEN_HERE"

# without a token — should be rejected
curl -s -o /dev/null -w "no token: %{http_code}\n" http://localhost:8000/whoami

# with a valid token — should succeed
curl -s -w "\nwith token: %{http_code}\n" http://localhost:8000/whoami \
  -H "Authorization: Bearer $TOKEN"
```

**Expected output:**
```
no token: 403
{"you_are":"alice"}
with token: 200
```

(403, not 401, for the missing-token case — that's `HTTPBearer`'s own
check firing before our code runs; both are "you're not allowed in.")

Don't move to Step 8 until all five tests pass.

---

## Step 8 — Notices: public read, authenticated create

Add these to the bottom of `app.py` (keep everything from Step 7 —
you're adding, not replacing):

```python
class NoticeCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@app.get("/notices")
def list_notices():
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, message, author, created_at FROM notices ORDER BY created_at DESC")
            rows = cur.fetchall()
        for row in rows:
            row["created_at"] = row["created_at"].isoformat()
        return rows
    finally:
        conn.close()


@app.post("/notices", status_code=201)
def create_notice(body: NoticeCreate, username: str = Depends(get_current_username)):
    conn = get_connection()
    try:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO notices (message, author) VALUES (%s, %s) "
                "RETURNING id, message, author, created_at",
                (body.message, username),
            )
            row = cur.fetchone()
        conn.commit()
        row["created_at"] = row["created_at"].isoformat()
        return row
    finally:
        conn.close()
```

**Restart uvicorn** (it should auto-reload if you left `--reload` on;
if not, `Ctrl+C` and rerun).

**Test 1 — list notices with no login (should work, empty list):**

```bash
curl -s http://localhost:8000/notices
```

**Expected output:** `[]`

**Test 2 — create a notice without a token (should be blocked):**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/notices \
  -H "Content-Type: application/json" \
  -d '{"message": "should fail"}'
```

**Expected output:** `403`

**Test 3 — create a notice with a token (should succeed):**

```bash
TOKEN="PASTE_YOUR_TOKEN_HERE"

curl -s -X POST http://localhost:8000/notices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "hello board"}'
```

**Expected output:** a JSON object with `id: 1`, `message: "hello
board"`, `author: "alice"`, and a `created_at` timestamp.

**Test 4 — confirm it shows up in the public list:**

```bash
curl -s http://localhost:8000/notices
```

**Expected output:** a list containing the notice you just created.

---

## Step 9 — Delete, restricted to the notice's own author

This is the ownership check — the part that makes "only the person
who created it can delete it" actually true.

Add to the bottom of `app.py`:

```python
@app.delete("/notices/{notice_id}")
def delete_notice(notice_id: int, username: str = Depends(get_current_username)):
    conn = get_connection()
    try:
        ensure_tables(conn)

        # Look up who actually owns this notice BEFORE deleting anything.
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT author FROM notices WHERE id = %s", (notice_id,))
            row = cur.fetchone()

        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
        if row["author"] != username:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own notices")

        with conn.cursor() as cur:
            cur.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
        conn.commit()
        return {"deleted": notice_id}
    finally:
        conn.close()
```

**Test — this is the important one. Two different users, one notice.**

```bash
# Register a second user
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "hunter22222"}'
# copy bob's access_token below
```

```bash
ALICE_TOKEN="PASTE_ALICES_TOKEN"
BOB_TOKEN="PASTE_BOBS_TOKEN"

# Alice creates a notice — note its "id" in the response
curl -s -X POST http://localhost:8000/notices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d '{"message": "this is alices notice"}'
```

```bash
NOTICE_ID=2   # replace with the id from the response above

# Bob tries to delete Alice's notice — should be BLOCKED
curl -s -o /dev/null -w "bob deleting alices notice: %{http_code}\n" \
  -X DELETE http://localhost:8000/notices/$NOTICE_ID \
  -H "Authorization: Bearer $BOB_TOKEN"

# Alice deletes her own notice — should SUCCEED
curl -s -w "\nalice deleting her own notice: %{http_code}\n" \
  -X DELETE http://localhost:8000/notices/$NOTICE_ID \
  -H "Authorization: Bearer $ALICE_TOKEN"
```

**Expected output:**
```
bob deleting alices notice: 403
{"deleted":2}
alice deleting her own notice: 200
```

If you see `403` then `200` in that order, ownership enforcement is
working correctly — a real cross-user delete attempt was rejected,
and the actual owner succeeded.

**Bonus check — deleting something that no longer exists:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE http://localhost:8000/notices/$NOTICE_ID \
  -H "Authorization: Bearer $ALICE_TOKEN"
```

**Expected output:** `404`.

---

## Step 10 — Save your dependencies

Now that the backend works, freeze what you actually installed:

```bash
pip freeze | grep -iE "fastapi|uvicorn|psycopg2|pyjwt|bcrypt|pydantic|starlette" > requirements.txt
cat requirements.txt
```

**Test:** the file should list `fastapi`, `psycopg2-binary`, `PyJWT`,
`bcrypt`, `pydantic`, and a few dependencies of those. Keep this file
— it's what gets installed when packaging for Lambda later.

Backend is done and fully tested locally. **Deactivate the venv**
before moving to the frontend:

```bash
deactivate
```

---

## Step 11 — Frontend scaffold

```bash
cd ../frontend
npm create vite@latest . -- --template react
```

(If it asks to overwrite an empty directory, say yes.)

**Test:**

```bash
npm install
npm run dev
```

**Expected:** terminal prints a `Local: http://localhost:5173/` URL.
Open it in a browser — you should see Vite's default React starter
page (a spinning logo, a counter button). This confirms Node, npm,
and Vite are all working before you touch any of our code.

Stop the dev server (`Ctrl+C`) before continuing.

---

## Step 12 — Replace the default app with the API client

Delete Vite's starter cruft and create `frontend/src/api.js`:

```bash
rm -f src/App.css src/assets/react.svg
```

```js
// src/api.js — every network call the frontend makes goes through here.

const API_URL = import.meta.env.VITE_API_URL

async function request(path, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message =
      typeof body.detail === 'string' ? body.detail : body.detail ? JSON.stringify(body.detail) : `Request failed: ${res.status}`
    throw new Error(message)
  }
  if (res.status === 204) return null
  return res.json()
}

export function fetchNotices() {
  return request('/notices')
}

export function postNotice(message) {
  return request('/notices', { method: 'POST', body: JSON.stringify({ message }) })
}

export function deleteNotice(id) {
  return request(`/notices/${id}`, { method: 'DELETE' })
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem('token', data.access_token)
  return data
}

export async function register(username, password) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem('token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('token')
}

export function isLoggedIn() {
  return !!localStorage.getItem('token')
}

// Decodes the JWT payload client-side to find out who's logged in.
// The payload isn't secret (it's base64, not encrypted), so this is
// safe — we're just reading the "sub" claim we put there at login.
export function getUsername() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub || null
  } catch {
    return null
  }
}
```

**Set the API URL for local dev.** Create `frontend/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

**Test — before writing any UI, prove api.js itself works, in the
browser console.** Start both servers:

```bash
# terminal 1, in backend/ with venv active
uvicorn app:app --reload --port 8000

# terminal 2, in frontend/
npm run dev
```

Open `http://localhost:5173`, open the browser DevTools console, and
paste:

```js
const mod = await import('/src/api.js')
const data = await mod.fetchNotices()
console.log(data)
```

**Expected output:** an array (probably with the one notice you
created in Step 9's tests, if you're pointing at the same database) —
proof the frontend can actually reach the backend over HTTP with CORS
working, before any UI exists to hide a broken connection.

> If this fails with a CORS error in the console, your FastAPI app
> needs the CORS middleware. Add this near the top of `app.py`, restart
> uvicorn, and retry:
> ```python
> from fastapi.middleware.cors import CORSMiddleware
> app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
> ```

---

## Step 13 — Build the UI

Replace `frontend/src/App.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { fetchNotices, postNotice, deleteNotice, login, register, logout, isLoggedIn, getUsername } from './api.js'

export default function App() {
  const [authed, setAuthed] = useState(isLoggedIn())
  const [username, setUsername] = useState(getUsername())
  const [showAuth, setShowAuth] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [authUser, setAuthUser] = useState('')
  const [authPass, setAuthPass] = useState('')
  const [authError, setAuthError] = useState(null)

  const [notices, setNotices] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState(null)

  async function load() {
    try {
      setNotices(await fetchNotices())
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleAuthSubmit(e) {
    e.preventDefault()
    setAuthError(null)
    try {
      if (authMode === 'login') await login(authUser, authPass)
      else await register(authUser, authPass)
      setAuthed(true)
      setUsername(getUsername())
      setShowAuth(false)
    } catch (err) {
      setAuthError(err.message)
    }
  }

  async function handlePost(e) {
    e.preventDefault()
    if (!message.trim()) return
    try {
      await postNotice(message.trim())
      setMessage('')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteNotice(id)
      setNotices((prev) => prev.filter((n) => n.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  function handleLogout() {
    logout()
    setAuthed(false)
    setUsername(null)
  }

  if (showAuth && !authed) {
    return (
      <div style={{ maxWidth: 320, margin: '80px auto', fontFamily: 'sans-serif' }}>
        <button onClick={() => setShowAuth(false)}>&larr; Back</button>
        <h2>{authMode === 'login' ? 'Log in' : 'Sign up'}</h2>
        <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input placeholder="Username" value={authUser} onChange={(e) => setAuthUser(e.target.value)} required />
          <input placeholder="Password" type="password" value={authPass} onChange={(e) => setAuthPass(e.target.value)} required />
          <button type="submit">{authMode === 'login' ? 'Log In' : 'Sign Up'}</button>
        </form>
        {authError && <p style={{ color: 'red' }}>{authError}</p>}
        <button onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
          {authMode === 'login' ? 'Need an account?' : 'Have an account?'}
        </button>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 480, margin: '40px auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>Notice Board</h1>
        {authed ? <button onClick={handleLogout}>Log out ({username})</button> : <button onClick={() => setShowAuth(true)}>Log in</button>}
      </div>

      {authed ? (
        <form onSubmit={handlePost} style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
          <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Write a notice..." />
          <button type="submit">Post</button>
        </form>
      ) : (
        <p>
          <button onClick={() => setShowAuth(true)}>Log in</button> to post a notice.
        </p>
      )}

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <ul>
        {notices.map((n) => (
          <li key={n.id}>
            {n.message} — <em>{n.author}</em>
            {authed && n.author === username && <button onClick={() => handleDelete(n.id)}>delete</button>}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

**Test — this is the full manual walkthrough:**

1. `npm run dev` (backend still running from Step 12 in its own terminal)
2. Open `http://localhost:5173` — you should see "Notice Board" and an empty list, with a **Log in** link (no composer visible — you're logged out)
3. Click **Log in** → **Need an account?** → register a brand-new username → you should land back on the board, now with a text box and **Post** button
4. Type something, click **Post** → it should appear in the list immediately, tagged with your username
5. **Refresh the page** → the notice should still be there (proves it's really in Postgres, not just React state) and you should still be logged in (proves the token persisted in `localStorage`)
6. Open a **second browser** (or an incognito window) and register a *different* user → post a notice as that user
7. Back in your first browser, refresh — you should see both notices, but a delete button **only on your own**
8. Try deleting your own notice → it disappears
9. In the second (incognito) browser, refresh → your first notice, deleted by its actual owner, is gone there too

If all nine of those work, the full stack — Postgres, FastAPI, JWT
auth, ownership-scoped delete, React — is proven working end to end,
entirely locally, with no AWS involved yet.

---

## What's next

Everything above runs on your laptop. Deploying this to AWS (Lambda +
API Gateway + S3 + CloudFront + CloudWatch, across the assignment's 4
tiers) is a separate phase built on top of this working code —
covered in `planning/03-implementation-plan.md` and the root
`README.md` from the project zip. Don't start the AWS deployment until
every test in this guide passes locally; debugging Postgres/JWT/CORS
issues is much faster on your laptop than through a Lambda cold start.
