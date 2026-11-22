from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, ComplianceCheck
from app.compliance.frameworks.cis_benchmark import cis_evaluator

router = APIRouter()

@router.get("/checks", response_model=List[Dict[str, Any]])
def get_compliance_checks(
    framework: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
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

    # Checks grow with every scan; an unbounded .all() hands a long-lived
    # tenant one ever-larger payload. Same skip/limit contract as the scan
    # and finding lists. Ordered newest-first so a page is stable.
    query = query.order_by(ComplianceCheck.checked_at.desc()).offset(skip).limit(limit)

    return [
        {
            "id": c.id,
            "scan_id": c.scan_id,
            "framework": c.framework,
            "control_id": c.control_id,
            "title": c.title,
            "status": c.status,
            "resource_id": c.resource_id,
            "checked_at": c.checked_at.isoformat() if c.checked_at else None
        }
        for c in query.all()
    ]

@router.get("/summary", response_model=Dict[str, float])
def get_compliance_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Yields aggregate posture percentages for frameworks with evaluated checks; empty when nothing has been scanned"""
    from app.compliance.checker import compliance_engine
    from app.database.models import Scan
    
    # A demo scan is a finished scan: its checks were evaluated, so it
    # counts here exactly like a real one. Filtering to COMPLETED only
    # left the dashboard's framework overview empty after every demo
    # scan — the main way the app is tried — even though checks existed.
    latest_scan = db.query(Scan).filter(
        Scan.organization_id == current_user.organization_id,
        Scan.status.in_(["COMPLETED", "DEMO_COMPLETED"])
    ).order_by(Scan.completed_at.desc()).first()
    
    if not latest_scan:
        # Nothing has been evaluated, so no framework earns a score.
        return {}
        
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.scan_id == latest_scan.id).all()
    # Control-level rows (one per CIS control, PASS or FAIL) are the
    # score basis when a scan wrote them: finding-derived rows are all
    # FAIL by construction, so scoring from them could never exceed 0%.
    # Scans from before control-level rows existed have none, and fall
    # back to all rows rather than showing nothing.
    control_checks = [c for c in checks
                      if isinstance(c.evidence, dict) and c.evidence.get("control_level")]
    scored = control_checks if control_checks else checks
    checks_list = [
        {"framework": c.framework, "status": c.status}
        for c in scored
    ]

    return compliance_engine.calculate_scores(checks_list)
