from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("", response_model=List[UserResponse])
def list_organization_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists real user accounts belonging to the caller's organization. No sample rows."""
    return db.query(User).filter(User.organization_id == current_user.organization_id).order_by(User.created_at.asc()).all()
