from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

from app.config.database import get_db
from app.database.models import User, Organization
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.user import UserCreate, UserResponse, Token

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Registers organization schema, user account, and returns credentials tokens"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )
        
    try:
        # Create organization
        org_id = str(uuid.uuid4())
        organization = Organization(
            id=org_id,
            name=payload.organization_name
        )
        db.add(organization)
        
        # Create user
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=payload.role or "user",
            organization_id=org_id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        
        # Query fresh copy
        db.refresh(new_user)
        
        # Generate tokens
        access_token = create_access_token(new_user.id)
        refresh_token = create_refresh_token(new_user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user=UserResponse.model_validate(new_user)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during registration flow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Check server logs."
        )

@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Validates login credentials and yields active authentication sessions"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password credentials."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )
        
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )
