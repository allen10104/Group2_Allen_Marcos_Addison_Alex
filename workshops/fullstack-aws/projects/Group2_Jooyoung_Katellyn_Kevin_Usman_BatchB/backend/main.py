from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.auth import router as auth_router
from backend.controllers.notices import router as notices_router

app = FastAPI(title="Notice Board API")

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
app.include_router(notices_router)


@app.get("/")
def health():
    return {"status": "ok"}
