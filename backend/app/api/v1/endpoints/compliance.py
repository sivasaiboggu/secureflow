from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, ComplianceCheck, Scan

router = APIRouter()

@router.get("/checks", response_model=List[Dict[str, Any]])
def get_compliance_checks(
    framework: Optional[str] = None,
    status: Optional[str] = None,
    scan_id: Optional[str] = Query(None, max_length=50),
    finished_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists compliance controls verified by scanning agents"""
    query = db.query(ComplianceCheck).join(Scan).filter(Scan.organization_id == current_user.organization_id)

    if finished_only:
        query = query.filter(Scan.status.in_(["COMPLETED", "DEMO_COMPLETED"]))
    if scan_id:
        query = query.filter(ComplianceCheck.scan_id == scan_id)
    if framework:
        query = query.filter(ComplianceCheck.framework == framework.upper())
    if status:
        query = query.filter(ComplianceCheck.status == status.upper())

    # Checks grow with every scan; an unbounded .all() hands a long-lived
    # tenant one ever-larger payload. Same skip/limit contract as the scan
    # and finding lists. Ordered newest-first so a page is stable.
    query = query.add_columns(Scan.status).order_by(ComplianceCheck.checked_at.desc(), ComplianceCheck.id).offset(skip).limit(limit)

    results = []
    for check, scan_status in query.all():
        evidence = check.evidence if isinstance(check.evidence, dict) else {}
        resources = evidence.get("violating_resources")
        results.append({
            "id": check.id,
            "scan_id": check.scan_id,
            "framework": check.framework,
            "control_id": check.control_id,
            "title": check.title,
            "status": check.status,
            "resource_id": check.resource_id,
            "checked_at": check.checked_at.isoformat() if check.checked_at else None,
            "sample": scan_status == "DEMO_COMPLETED",
            "control_level": bool(evidence.get("control_level")),
            "violating_resources": [item for item in resources if isinstance(item, str)] if isinstance(resources, list) else [],
        })
    return results


@router.get("/summary", response_model=Dict[str, float])
def get_compliance_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Yields aggregate posture percentages for frameworks with evaluated checks; empty when nothing has been scanned"""
    from app.compliance.checker import compliance_engine
    
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
