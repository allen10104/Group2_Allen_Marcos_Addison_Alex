"""
Notice Board API — FastAPI app assembled from the `notice_board` package,
running on Lambda behind API Gateway via Mangum (see terraform/main.tf,
handler = "app.handler").

Route modules:
    notice_board/routers/auth.py     POST /auth/register, POST /auth/login
    notice_board/routers/notices.py  GET/POST /notices, PUT/PATCH/DELETE /notices/{id}

Runtime configuration (env vars) is documented in notice_board/config.py
and notice_board/database.py.

Do not modify this file when working on Tier 4 (observability) — that
tier is implemented entirely in Terraform / infrastructure.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from notice_board.routers import auth, notices

app = FastAPI(title="Notice Board API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notices.router)

handler = Mangum(app, lifespan="off")
