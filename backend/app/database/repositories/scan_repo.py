from sqlalchemy.orm import Session
from typing import Optional, List
from app.database.models import Scan

class ScanRepository:
    def get_by_id(self, db: Session, scan_id: str) -> Optional[Scan]:
        return db.query(Scan).filter(Scan.id == scan_id).first()

    def list_by_organization(self, db: Session, org_id: str, skip: int = 0, limit: int = 50) -> List[Scan]:
        return db.query(Scan).filter(Scan.organization_id == org_id)\
                             .order_by(Scan.created_at.desc())\
                             .offset(skip).limit(limit).all()

    def get_latest_completed(self, db: Session, org_id: str) -> Optional[Scan]:
        return db.query(Scan).filter(
            Scan.organization_id == org_id,
            Scan.status == "COMPLETED"
        ).order_by(Scan.completed_at.desc()).first()

scan_repo = ScanRepository()
