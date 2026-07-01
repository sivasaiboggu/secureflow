from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, ComplianceCheck
from app.compliance.frameworks.cis_benchmark import cis_evaluator

router = APIRouter()

@router.get("/checks", response_model=List[Dict[str, Any]])
def get_compliance_checks(
    framework: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists compliance controls verified by scanning agents"""
    from app.database.models import Scan
    query = db.query(ComplianceCheck).join(Scan).filter(Scan.organization_id == current_user.organization_id)
    
    if framework:
        query = query.filter(ComplianceCheck.framework == framework.upper())
    if status:
        query = query.filter(ComplianceCheck.status == status.upper())
        
    return [
        {
            "id": c.id,
            "scan_id": c.scan_id,
            "framework": c.framework,
            "control_id": c.control_id,
            "title": c.title,
            "status": c.status,
            "resource_id": c.resource_id,
            "checked_at": c.checked_at.isoformat()
        }
        for c in query.all()
    ]

@router.get("/summary", response_model=Dict[str, float])
def get_compliance_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Yields aggregate posture percentages across categories"""
    from app.compliance.checker import compliance_engine
    from app.database.models import Scan
    
    latest_scan = db.query(Scan).filter(
        Scan.organization_id == current_user.organization_id,
        Scan.status == "COMPLETED"
    ).order_by(Scan.completed_at.desc()).first()
    
    if not latest_scan:
        return {"CIS": 100.0, "NIST": 100.0, "PCI_DSS": 100.0, "HIPAA": 100.0, "GDPR": 100.0}
        
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.scan_id == latest_scan.id).all()
    checks_list = [
        {"framework": c.framework, "status": c.status}
        for c in checks
    ]
    
    return compliance_engine.calculate_scores(checks_list)

from typing import Optional
