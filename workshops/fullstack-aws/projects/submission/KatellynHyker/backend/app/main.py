""" Entry point for the FastAPI application. """

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.controllers.authController import router as auth_router
from app.controllers.commentController import comments_router, notice_comments_router
from app.controllers.likeController import router as like_router
from app.controllers.noticeController import router as notice_router
from app.controllers.userController import router as user_router
from app.models.database import init_db
from app.models.exceptions import (
    AppError,
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

app = FastAPI(title="Notice Board API")

app.include_router(auth_router)
app.include_router(notice_router)
app.include_router(user_router)
app.include_router(notice_comments_router)
app.include_router(comments_router)
app.include_router(like_router)

_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """ Initialize the database on startup """
    init_db()

@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    """ Handle custom application errors """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """ Handle HTTP exceptions """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """ Handle request validation errors """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(DuplicateError)
def duplicate_error_handler(request: Request, exc: DuplicateError):
    """ Handle duplicate resource errors """
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail},
    )

@app.exception_handler(ForbiddenError)
def forbidden_error_handler(request: Request, exc: ForbiddenError):
    """ Handle forbidden access errors """
    return JSONResponse(
        status_code=403,
        content={"detail": exc.detail},
    )

@app.exception_handler(NotFoundError)
def not_found_error_handler(request: Request, exc: NotFoundError):
    """ Handle resource not found errors """
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )

@app.exception_handler(UnauthorizedError)
def unauthorized_error_handler(request: Request, exc: UnauthorizedError):
    """ Handle unauthorized access errors """
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
    )

@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    """ Handle validation errors """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    """ Catch-all so an unexpected bug returns a clean 500 instead of a
    raw stack trace / connection reset. """
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )