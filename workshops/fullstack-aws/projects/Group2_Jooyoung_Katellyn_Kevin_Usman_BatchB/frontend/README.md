# Notice Board Frontend

React + TypeScript (Vite) client for the Group2 Notice Board API.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # optional; defaults to http://localhost:8000
npm run dev
```

Open http://localhost:5173. Run the FastAPI backend on port 8000 first.

## Features

- Auth context with JWT in memory + `localStorage`
- Axios interceptor attaches `Authorization: Bearer <token>`
- Top navbar with Log in / Log out
- Noticeboard: guests view-only; users manage own notices; admins manage all
- Login page (`/login`)
