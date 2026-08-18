import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.controllers.auth import router as auth_router
from backend.controllers.notices import router as notices_router

app = FastAPI(title="Notice Board API")

# Local uvicorn needs CORS here. On Lambda, API Gateway owns CORS so we do
# not send a second Access-Control-Allow-Origin (browsers reject duplicates).
if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
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


@app.options("/{full_path:path}")
def cors_preflight(full_path: str) -> Response:
    # HTTP API $default forwards OPTIONS to Lambda. Without this, FastAPI
    # returns 405 and the browser blocks login (POST JSON is a CORS preflight).
    # API Gateway still attaches Access-Control-Allow-* on the way out.
    return Response(status_code=204)


@app.get("/")
def health():
    return {"status": "ok"}
