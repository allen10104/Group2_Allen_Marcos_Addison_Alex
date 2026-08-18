# THis file contains the main entry point for the SyncUp backend application, which is built using FastAPI.
# It sets up the application, configures middleware, and includes various routers for handling different API endpoints.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers import auth_controller, invite_controller, notices_controller, users_controller
from app.database import connect, disconnect, ensure_indexes

# Calls teh database connect()/disconnect()/ensure_indexes() in database.py to manage the database connection and ensure indexes are created when the application starts up.
@asynccontextmanager
async def lifespan(app: FastAPI):
    connect()
    await ensure_indexes()
    yield
    disconnect()

# CREATES THE FASTAPI APPLICATION INSTANCE WITH THE TITLE "SyncUp API" AND THE LIFESPAN CONTEXT MANAGER DEFINED ABOVE.
app = FastAPI(title="SyncUp API", lifespan=lifespan)

# THis middleware is added to the application to handle Cross-Origin Resource Sharing (CORS) requests.
# It allows requests from origins specified in the `settings.cors_origins_list`, and it permits credentials, 
# all HTTP methods, and all headers in cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    # Only allow origins specified in the settings.cors_origins_list to make cross-origin requests to the API.
    allow_origins=settings.cors_origins_list,
    # Permits browers to include credentials (like cookies or authorization headers) in cross-origin requests.
    allow_credentials=True,
    # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.) in cross-origin requests.
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router)
app.include_router(users_controller.router)
app.include_router(notices_controller.router)
app.include_router(invite_controller.router)

# The `/health` endpoint is a simple health check route that returns a JSON response indicating that the application is running and healthy.
@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}