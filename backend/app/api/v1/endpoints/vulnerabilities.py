from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter()

@router.get("", response_model=List[VulnerabilityResponse])
def get_vulnerabilities(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches list of active vulnerabilities and cloud findings, supporting severity filters"""
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
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    return vuln

@router.post("/remediate", response_model=RemediationResponse)
def trigger_automated_remediation(
    payload: RemediationApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes automated remediation scripts (Terraform/Ansible) to repair security issues"""
    try:
        remediation = scan_service.apply_remediation(db, payload.vulnerability_id, current_user.email)
        return remediation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Remediation fail: {e}")

@router.post("/analyze-log")
def classify_text_log(payload: LogAnalysisRequest):
    """Applies NLP model to identify suspicious commands or compromised log scripts"""
    result = ml_service.scan_log_for_threats(payload.log_payload)
    return result

@router.post("/analyze-metrics")
def detect_metric_anomaly(payload: MetricAnalysisRequest):
    """Applies Neural Autoencoders to identify anomalous metric streams in API counts"""
    result = ml_service.analyze_api_logs(payload.metrics)
    return result
