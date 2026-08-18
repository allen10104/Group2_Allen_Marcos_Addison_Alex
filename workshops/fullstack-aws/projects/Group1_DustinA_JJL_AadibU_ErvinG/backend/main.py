from fastapi import FastAPI
from routers import auth_routes, users, notices
import models, schemas, database, auth
from models import Department
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Notice Board API", description="API for managing notices", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(users.router)
app.include_router(notices.router)
    