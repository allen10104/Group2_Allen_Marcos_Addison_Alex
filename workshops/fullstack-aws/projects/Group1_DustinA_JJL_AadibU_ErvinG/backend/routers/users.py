from fastapi import APIRouter, Depends
import models, schemas, auth, database

router = APIRouter(prefix="/users", tags=["users"])  

@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user