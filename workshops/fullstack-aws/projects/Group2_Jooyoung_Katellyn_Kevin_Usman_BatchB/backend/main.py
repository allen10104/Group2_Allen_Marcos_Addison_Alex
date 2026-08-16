from fastapi import FastAPI

from backend.controllers.auth import router as auth_router
from backend.controllers.notices import router as notices_router

app = FastAPI(title="Notice Board API")
app.include_router(auth_router)
app.include_router(notices_router)


@app.get("/")
def health():
    return {"status": "ok"}
