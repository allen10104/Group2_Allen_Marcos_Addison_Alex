# Running Notice Board locally

Local-only tooling to run the real backend + frontend against a local Postgres,
without touching AWS.

The backend is now a real FastAPI app (`backend/app/`) — no adapter needed,
just run it directly with `uvicorn`.

## 1. Start Docker Desktop, then local Postgres

```powershell
docker ps                 # if this errors, start Docker Desktop first and re-check
cd local
docker compose up -d
docker compose ps         # wait until STATUS shows "healthy"
cd ..
```

## 2. Backend — install deps and run the API

```powershell
python -m venv local/venv
local/venv/Scripts/Activate.ps1     # Git Bash: source local/venv/Scripts/activate
pip install -r backend/requirements.txt

cd backend
Copy-Item .env.example .env         # Git Bash: cp .env.example .env
# defaults in .env.example already match docker-compose.yml (localhost:5432,
# noticeboard/noticeboard_app/localdev) — no edits needed for local dev.
uvicorn app.main:app --reload --port 8000
cd ..
```

Leave this running. It listens on `http://localhost:8000`. Image uploads
work locally too — with `S3_UPLOADS_BUCKET` left blank, they're written to
`backend/_local_uploads/` and served back at `http://localhost:8000/uploads/...`.

## 3. Frontend (new terminal)

```powershell
cd frontend
npm install
Copy-Item .env.example .env     # Git Bash: cp .env.example .env
```

Edit `frontend/.env`:
```
VITE_API_URL=http://localhost:8000/api
```

```powershell
npm run dev
```

Open the printed URL (usually `http://localhost:5173`) and use the UI to post
notices — with an image and an expiry — and delete them.

## Verify data actually lands in Postgres

```bash
docker exec -it noticeboard-local-pg psql -U noticeboard_app -d noticeboard -c "select * from notices;"
```

## Test expiry cleanup without waiting on cron

```powershell
cd backend
../local/venv/Scripts/python.exe cleanup_expired.py
```

## Cleanup

```powershell
# Ctrl+C the frontend dev server and the uvicorn process
cd local
docker compose down        # keeps data
# docker compose down -v   # wipes data too
```

## Notes / gotchas

- Editing `frontend/.env` requires restarting `npm run dev` — Vite only reads it at startup.
- If port 5432 or 8000 is already taken, change it in `docker-compose.yml`/`backend/.env` together.
- `backend/_local_uploads/` is local-only and gitignored — it's not what production uses (production writes to S3).
