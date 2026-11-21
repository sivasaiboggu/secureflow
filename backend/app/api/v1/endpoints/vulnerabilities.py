from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User, Vulnerability, Remediation
from app.schemas.vulnerability import (
    VulnerabilityResponse, RemediationApply, RemediationResponse, 
    LogAnalysisRequest, MetricAnalysisRequest
)
from app.services.scan_service import scan_service
from app.services.ml_service import ml_service

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
VALID_VULNERABILITY_STATUSES = {"OPEN", "IN_PROGRESS", "REMEDIATED", "IGNORED"}

router = APIRouter()

@router.get("", response_model=List[VulnerabilityResponse])
def get_vulnerabilities(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches list of active vulnerabilities and cloud findings, supporting severity filters"""
    # An unknown severity or status previously filtered everything out and
    # returned an empty list, which looked identical to "no findings".
    # Reject it so a typo or a stale client value is visible immediately.
    # (Literal 400: the `status` query parameter shadows the imported
    # fastapi.status module inside this function.)
    if severity is not None and severity.upper() not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}.",
        )
    if status is not None and status.upper() not in VALID_VULNERABILITY_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_VULNERABILITY_STATUSES))}.",
        )
    vulnerabilities = scan_service.list_vulnerabilities(
        db, current_user.organization_id, severity, status, skip, limit
    )
    return vulnerabilities

@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
def get_vulnerability_details(
    vulnerability_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full information for a security finding, including generated Terraform fix blocks"""
    vuln = scan_service.get_vulnerability(db, vulnerability_id, current_user.organization_id)
    if not vuln:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    return vuln

@router.post("/remediate", response_model=RemediationResponse)
def trigger_automated_remediation(
    payload: RemediationApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

@router.post("/analyze-log")
def classify_text_log(payload: LogAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Heuristic CloudTrail log review. An optional local model requires separate validation; not verified threat detection."""
    try:
        result = ml_service.scan_log_for_threats(payload.log_payload)
    except ValueError as e:
        # A malformed payload is a client error, not a server failure.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result

@router.post("/analyze-metrics")
def detect_metric_anomaly(payload: MetricAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Reviews eight API metrics with a local autoencoder when reviewed artifacts are loaded; otherwise reports the detector as unavailable."""
    try:
        result = ml_service.analyze_api_logs(payload.metrics)
    except ValueError as e:
        # Wrong count or non-finite values are client errors, not server
        # failures: previously this surfaced as a bare 500.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result
