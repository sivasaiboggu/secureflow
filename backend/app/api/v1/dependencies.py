from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.database.models import User
from app.core.exceptions import CredentialsException, PermissionException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db_session() -> Session:
    """Convenience getter returning active DB session context"""
    from app.config.database import SessionLocal
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def get_current_active_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """Identifies and returns the validated JWT user payload context"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise CredentialsException("User account not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")
        
    return user

class VerifyUserHasRole:
    """Verifies that the request user context holds the correct security roles"""
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
        
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if user.role not in self.allowed_roles:
            raise PermissionException("Insufficient access roles")
        return user
