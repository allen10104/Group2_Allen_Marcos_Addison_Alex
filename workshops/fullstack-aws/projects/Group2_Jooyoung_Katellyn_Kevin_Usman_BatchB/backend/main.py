from fastapi import FastAPI

from backend.controllers.notices import router as notices_router

app = FastAPI(title="Notice Board API")
app.include_router(notices_router)


@app.get("/")
def health():
    return {"status": "ok"}
