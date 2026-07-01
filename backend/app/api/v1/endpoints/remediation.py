from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, Remediation, Vulnerability
from app.schemas.vulnerability import RemediationApply, RemediationResponse
from app.services.scan_service import scan_service

router = APIRouter()

@router.post("/apply", response_model=RemediationResponse)
def apply_remediation_patch(payload: RemediationApply, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Applies auto-remediation (generating and running Terraform fixes) for a finding"""
    try:
        remediation = scan_service.apply_remediation(db, payload.vulnerability_id, current_user.email)
        return remediation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Apply failed: {e}")

@router.get("/history", response_model=List[RemediationResponse])
def get_remediation_runs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists historical remediation tasks executed in the organization"""
    from app.database.models import Scan
    runs = db.query(Remediation).join(Vulnerability).join(Scan).filter(
        Scan.organization_id == current_user.organization_id
    ).all()
    return runs
