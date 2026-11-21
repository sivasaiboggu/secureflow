from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    """Saves a Terraform plan for review. Does not execute infrastructure changes."""
    try:
        remediation = scan_service.apply_remediation(db, payload.vulnerability_id, current_user.email, current_user.organization_id)
        return remediation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Raw driver/database exceptions can carry SQL parameters or secret-bearing
        # URLs. Clients get a fixed diagnostic; details stay out of the response.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The remediation plan could not be saved. Review the finding and try again.") from None

@router.get("/history", response_model=List[RemediationResponse])
def get_remediation_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists saved remediation review plans for the organization. Plans are not executed repairs."""
    from app.database.models import Scan
    # Plans accumulate one per finding; bound the response like the other
    # list endpoints instead of returning every row ever saved.
    runs = db.query(Remediation).join(Vulnerability).join(Scan).filter(
        Scan.organization_id == current_user.organization_id
    ).offset(skip).limit(limit).all()
    return runs
