""" Routes for authentication and authorization """

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import LoginRequest, RegisterRequest
from app.services import authService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return authService.register(request, db)

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return authService.login(request, db)