from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, CloudAccount, Scan
from app.schemas.scan import ScanCreate, ScanResponse, CloudAccountCreate, CloudAccountResponse
from app.services.scan_service import scan_service

router = APIRouter()

@router.post("", response_model=ScanResponse)
def trigger_new_scan(payload: ScanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Triggers an async cloud security posture scan for the specified credentials account"""
    try:
        scan = scan_service.trigger_scan(db, payload.cloud_account_id, current_user.organization_id)
        return scan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to dispatch: {e}")

@router.get("", response_model=List[ScanResponse])
def get_scans_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists recent scans executed within the tenant organization"""
    scans = scan_service.list_scans(db, current_user.organization_id, skip, limit)
    return scans

@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_details(scan_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieves execution state, compliance score, and findings count of a specific scan"""
    scan = scan_service.get_scan(db, scan_id)
    if not scan or scan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")
    return scan

@router.post("/cloud-accounts", response_model=CloudAccountResponse)
def register_cloud_account(payload: CloudAccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Saves connection credentials profile for AWS, GCP, or Azure environments"""
    # Check if duplicate name
    dup = db.query(CloudAccount).filter(
        CloudAccount.name == payload.name,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="Cloud account name already registered.")
        
    account_id = str(uuid.uuid4())
    account = CloudAccount(
        id=account_id,
        name=payload.name,
        provider=payload.provider.lower(),
        organization_id=current_user.organization_id,
        credentials=payload.credentials,
        is_active=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@router.get("/cloud-accounts", response_model=List[CloudAccountResponse])
def list_cloud_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns active cloud connector credentials registered inside user's tenant organization"""
    accounts = db.query(CloudAccount).filter(CloudAccount.organization_id == current_user.organization_id).all()
    return accounts
