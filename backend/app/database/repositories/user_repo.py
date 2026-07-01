from sqlalchemy.orm import Session
from typing import Optional, List
from app.database.models import User

class UserRepository:
    def get_by_id(self, db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def list_by_organization(self, db: Session, org_id: str) -> List[User]:
        return db.query(User).filter(User.organization_id == org_id).all()

user_repo = UserRepository()
