from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, CloudAccount, Scan
from app.schemas.scan import ScanCreate, ScanResponse, CloudAccountCreate, CloudAccountResponse
from app.services.scan_service import scan_service, ScanDispatchUnknown

from app.security.credential_store import seal_credentials, CredentialStorageError

router = APIRouter()

@router.post("", response_model=ScanResponse)
def trigger_new_scan(payload: ScanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Triggers an async cloud security posture scan for the specified credentials account"""
    try:
        scan = scan_service.trigger_scan(db, payload.cloud_account_id, current_user.organization_id)
        return scan
    except ScanDispatchUnknown as error:
        raise HTTPException(status_code=503, detail={
            "code": "QUEUE_ACCEPTANCE_UNKNOWN", "scan_id": error.scan_id,
            "message": str(error)
        }) from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start the scan. Check its status before trying again.")

@router.get("", response_model=List[ScanResponse])
def get_scans_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists recent scans executed within the tenant organization"""
    scans = scan_service.list_scans(db, current_user.organization_id, skip, limit)
    return scans

@router.post("/cloud-accounts", response_model=CloudAccountResponse)
def register_cloud_account(payload: CloudAccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Saves an AWS connector or explicit sample-data profile"""
    if payload.provider.lower() != "aws":
        raise HTTPException(status_code=400, detail="Only AWS connections are supported for scans.")
    mode = payload.credentials.get("scan_mode", "real")
    if mode not in ("real", "demo"):
        raise HTTPException(status_code=400, detail="Scan mode must be real or demo.")
    if mode == "real" and not (payload.credentials.get("aws_access_key_id") and payload.credentials.get("aws_secret_access_key")):
        raise HTTPException(status_code=400, detail="AWS credentials are required unless demo mode is selected.")
    # Check if duplicate name
    dup = db.query(CloudAccount).filter(
        CloudAccount.name == payload.name,
        CloudAccount.organization_id == current_user.organization_id
    ).first()
    if dup:
        raise HTTPException(status_code=400, detail="Cloud account name already registered.")
        
    account_id = str(uuid.uuid4())
    try:
        stored_credentials = seal_credentials(payload.credentials, account_id, current_user.organization_id, payload.provider)
    except CredentialStorageError as error:
        raise HTTPException(status_code=503, detail=str(error)) from None
    account = CloudAccount(
        id=account_id,
        name=payload.name,
        provider=payload.provider.lower(),
        organization_id=current_user.organization_id,
        credentials=stored_credentials,
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


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_details(scan_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieves execution state, compliance score, and findings count of a specific scan"""
    scan = scan_service.get_scan(db, scan_id)
    if not scan or scan.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")
    return scan
