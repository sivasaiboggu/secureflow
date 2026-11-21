from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

from app.config.database import get_db
from app.config.settings import settings
from app.database.models import User, Organization
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.user import UserCreate, UserResponse, Token, RefreshRequest

logger = logging.getLogger(__name__)

def _normalize_email(email: str) -> str:
    """Email addresses are stored and matched lowercase without surrounding
    whitespace, so case or spacing differences never create duplicate
    accounts or failed logins."""
    return email.strip().lower()

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Registers organization schema, user account, and returns credentials tokens"""
    # Check if user already exists. Rows written before input normalization
    # (or by any future writer) may store mixed case, and email identity is
    # case-insensitive, so the duplicate check must be too. Exact-match here
    # would let a normalized duplicate of a legacy row through.
    email = _normalize_email(payload.email)
    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
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
        # The registrant founds a new organization, so the server assigns the
        # founder role. A client-supplied role is never trusted: stored roles
        # feed RBAC checks, and accepting them would be self-assigned privilege.
        new_user = User(
            id=user_id,
            email=email,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            role="admin",
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
    except IntegrityError:
        # The pre-check above and this commit are not atomic: two
        # concurrent registrations for the same email can both pass the
        # check, and the loser's commit then hits the unique constraint.
        # That is a duplicate registration, not a server failure — answer
        # 400 like the pre-check does instead of a generic 500.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        ) from None
    except Exception:
        db.rollback()
        # Driver errors can carry SQL parameters, DSNs or account details.
        logger.error("Registration could not be completed; rolled back.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Check server logs."
        ) from None

@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Validates login credentials and yields active authentication sessions"""
    email = _normalize_email(form_data.username)
    # Case-insensitive read: a mixed-case row stored before normalization must
    # still be able to sign in instead of being locked out by its own casing.
    user = db.query(User).filter(func.lower(User.email) == email).first()
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

@router.post("/refresh", response_model=Token)
def refresh_access_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Exchanges a refresh token for a new short-lived access token.

    Refresh tokens are minted at login/register but previously had no
    exchange endpoint, so every session silently died after 30 minutes and
    the user had to sign in again. Only tokens carrying type "refresh" are
    accepted here; an access token (or a token without a type) is rejected,
    mirroring the rule in get_current_user. The refresh token itself is
    stateless and is returned unchanged — rotation would need server-side
    storage, which this app does not have.
    """
    try:
        token_payload = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = token_payload.get("sub")
        if user_id is None or token_payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        refresh_token=payload.refresh_token,
        user=UserResponse.model_validate(user)
    )
