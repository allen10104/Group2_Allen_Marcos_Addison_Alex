from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import connect_to_db, disconnect_from_db
from controllers.auth_controller import router as auth_router
from controllers.notice_controller import router as notice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_db()
    yield
    await disconnect_from_db()

app = FastAPI(lifespan=lifespan)

# Allow the local Vite dev server (and its 127.0.0.1 alias) to call this API
# during development. Add your deployed frontend's origin here once it exists.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(notice_router)