"""
Entry point for data management system REST API (FastAPI).

This file is responsible ONLY for:

- creating the FastAPI app instance
- wiring together the routers built by the controllers/ layer
- app-level metadata and a health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.customer_controller import router as customer_router
from controllers.account_controller import router as account_router
from controllers.transaction_controller import router as transaction_router
from controllers.auth_controller import router as auth_router
from controllers.branch_manager_controller import router as branch_manager_router
from controllers.user_controller import router as user_router

from models.database import init_db


# Create the main FastAPI application and define its API metadata.
server = FastAPI(
    title="Bank Management System API",
    description="RESTful API for managing customers, accounts, and transactions.",
    version="1.0.0",
)


# Allow the local frontend development server to communicate with the API.
# CORS is required because the frontend and backend run on different origins.
server.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create the database tables when the application starts.
# Existing tables are left unchanged.
init_db()


# Register each controller's routes under its appropriate API prefix.
# Controllers contain the endpoint logic while main.py only connects them
# to the main FastAPI application.
server.include_router(
    customer_router,
    prefix="/api/v1/customers",
    tags=["Customers"]
)

server.include_router(
    account_router,
    prefix="/api/v1/accounts",
    tags=["Accounts"]
)

server.include_router(
    transaction_router,
    prefix="/api/v1/transactions",
    tags=["Transactions"]
)

server.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

server.include_router(
    branch_manager_router,
    prefix="/api/v1/branch-managers",
    tags=["Branch Managers"]
)

server.include_router(
    user_router,
    prefix="/api/v1/users",
    tags=["Users"]
)


# Provide a simple health check endpoint to confirm that the API is running.
@server.get("/", tags=["Health"])
def health_check():
    """Simple liveness check to confirm the API is up."""
    return {"status": "ok", "service": "Bank Management System API"}


# Start the Uvicorn development server when this file is run directly.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:server",
        host="0.0.0.0",
        port=8000,
        reload=True
    )